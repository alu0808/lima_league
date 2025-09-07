# payments/services/mp.py
import mercadopago
from django.conf import settings


def mp_sdk():
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


def create_preference_for_match(payment, match, user, notify_url: str):
    sdk = mp_sdk()
    ext_ref = str(payment.public_id)

    data = {
        "items": [{
            "title": match.title or f"Partido #{match.id}",
            "quantity": 1,
            "currency_id": payment.currency,  # 'PEN'
            "unit_price": float(payment.amount),
        }],
        "payer": {
            "email": user.email or "noemail@example.com",
            "name": user.first_name or "",
            "surname": user.last_name or "",
        },
        "external_reference": ext_ref
    }

    success = getattr(settings, "FRONT_SUCCESS_URL", "")
    if success:  # solo si hay success definido
        data["back_urls"] = {
            "success": settings.FRONT_SUCCESS_URL,
            "failure": getattr(settings, "FRONT_FAILURE_URL", success),
            "pending": getattr(settings, "FRONT_PENDING_URL", success),
        }
        data["auto_return"] = "approved"  # <-- SOLO si hay success

    if notify_url:
        data["notification_url"] = notify_url

    # Checkout Pro - Preference
    res = sdk.preference().create(data)
    # Mercado Pago SDK suele devolver {"status": 201, "response": {...}} en éxito
    status_code = res.get("status")
    body = res.get("response", {})

    if status_code not in (200, 201):
        # Devuelve el error tal cual para que lo veas en la API
        raise RuntimeError(f"MercadoPago error {status_code}: {body}")

    # Asegura campos clave
    if not body.get("id") or (not body.get("init_point") and not body.get("sandbox_init_point")):
        raise RuntimeError(f"MercadoPago response missing fields: {body}")

    return body
