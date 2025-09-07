# payments/views.py
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from accounts.utils.authentication import DeviceTokenAuthentication
from config.responses import ok, error
from matches.api.models import Enrollment
from matches.models import Match, MatchStatus
from matches.services.enrollments import join_match
from .models import Payment, PaymentStatus
from .serializers import PaymentCreateSerializer, PaymentSerializer
from ..services.mp import create_preference_for_match, mp_sdk


class CreateCheckoutView(APIView):
    """
    Crea Payment + Preference (Checkout Pro).
    Devuelve init_point (URL de MP). El front redirige allí o inserta el botón embebido.
    """
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        ser = PaymentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        match_identifier = ser.validated_data["match_identifier"]

        match = get_object_or_404(Match, match_identifier=match_identifier)
        if match.status != MatchStatus.PUBLISHED:
            return error("Partido no disponible para pago", status_code=400)

        # PRE-CHECK de cupos
        current = Enrollment.objects.filter(match=match, is_active=True).count()
        if current >= match.capacity:
            return error("No hay cupos disponibles para este partido.", status_code=409)

        # 1) ya inscrito -> bloquear
        if Enrollment.objects.filter(match=match, user=request.user, is_active=True).exists():
            return error("Ya estás inscrito en este partido.", status_code=409)

        # 2) existe pago pendiente/en proceso -> reusar
        existing_pending = Payment.objects.filter(
            user=request.user, match=match,
            status__in=[PaymentStatus.PENDING]
        ).order_by("-created_at").first()
        if existing_pending:
            return ok(PaymentSerializer(existing_pending).data, message="Ya tienes un pago pendiente")

        payment = Payment.objects.create(
            user=request.user,
            match=match,
            amount=match.price_amount,
            currency=match.price_currency,
            external_reference="",  # se setea tras crear la fila
        )
        payment.external_reference = str(payment.public_id)
        payment.save(update_fields=["external_reference"])

        notify_url = settings.PUBLIC_BASE_URL.rstrip("/") + "/api/payments/mercadopago/webhook"

        try:
            pref = create_preference_for_match(payment, match, request.user, notify_url)
        except Exception as e:
            # Borra el payment o déjalo en pending pero muestra error
            return error(f"No se pudo crear preferencia: {e}", status_code=400)

        payment.preference_id = pref.get("id", "")
        payment.init_point = pref.get("init_point", "")
        payment.sandbox_init_point = pref.get("sandbox_init_point", "")
        payment.save(update_fields=["preference_id", "init_point", "sandbox_init_point"])

        return ok(PaymentSerializer(payment).data, message="Checkout creado")


@method_decorator(csrf_exempt, name="dispatch")
class MercadoPagoWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request):
        qp = request.query_params
        body = request.data if isinstance(request.data, dict) else {}

        # MP puede mandar formato nuevo (type=payment&data.id) o viejo (topic=payment&id)
        topic = qp.get("type") or qp.get("topic")
        if topic == "merchant_order":
            # no lo usamos; respondemos 200 para evitar reintentos
            return ok({"detail": "merchant_order ignored"}, message="OK")

        payment_id = (
                qp.get("data.id")
                or (body.get("data") or {}).get("id")
                or (qp.get("id") if (qp.get("topic") == "payment") else None)
        )
        if not payment_id:
            # sin payment_id, no hay nada útil que procesar
            return ok({"detail": "ignored"}, message="No payment_id")

        # Consultamos a MP para obtener el estado real
        sdk = mp_sdk()
        resp = sdk.payment().get(payment_id)
        if resp.get("status") != 200:
            return error("Cannot fetch payment", status_code=400)

        pr = resp["response"]
        ext_ref = pr.get("external_reference")
        mp_status = pr.get("status")  # approved | rejected | pending | in_process | cancelled | ...

        # bloqueamos la fila del Payment por external_reference
        payment = Payment.objects.select_for_update().filter(external_reference=ext_ref).first()
        if not payment:
            # puede pasar si borraron el registro; respondemos 200 para no reintentar
            return ok({"detail": "unknown external_reference"}, message="OK")

        # Idempotencia: si ya resolvimos definitivamente este pago, solo sincronizamos campos de MP
        if payment.status in (PaymentStatus.APPROVED, PaymentStatus.FAILED_CAPACITY, PaymentStatus.REJECTED):
            payment.mp_payment_id = str(payment_id)
            payment.mp_status = mp_status
            payment.save(update_fields=["mp_payment_id", "mp_status", "updated_at"])
            return ok({"status": payment.status}, message="Webhook processed")

        # Actualizamos campos MP del Payment
        payment.mp_payment_id = str(payment_id)
        payment.mp_status = mp_status

        if mp_status in ("approved", "accredited"):
            # Regla: si YA está inscrito, no volvemos a inscribir.
            if Enrollment.objects.filter(user=payment.user, match_id=payment.match_id, is_active=True).exists():
                payment.status = PaymentStatus.APPROVED
                payment.save(update_fields=["status", "mp_payment_id", "mp_status", "updated_at"])
                return ok({"status": payment.status, "note": "already_enrolled"}, message="Webhook processed")

            # Caso normal: inscribir (respeta cupos e idempotencia interna)
            try:
                join_match(payment.user, payment.match_id)
                payment.status = PaymentStatus.APPROVED
            except Exception:
                # si no hay cupos u otra validación del join falla
                payment.status = PaymentStatus.FAILED_CAPACITY

        elif mp_status in ("rejected", "cancelled"):
            payment.status = PaymentStatus.REJECTED
        else:
            # pending / in_process / otros
            payment.status = PaymentStatus.PENDING

        payment.save()
        return ok({"status": payment.status}, message="Webhook processed")
