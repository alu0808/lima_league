# accounts/views.py
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    DocumentType, City, District, FootballPosition, DominantFoot, TermsAndConditions
)
from accounts.services.sessions import logout_by_token, logout_all, upsert_session
from config.responses import created, ok, error
from matches.api.models import Team
from .serializers import (
    RegisterSerializer, UserSerializer, ChangePasswordSerializer, ProfileUpdateSerializer, LoginByDocumentSerializer
)
from ..utils.authentication import DeviceTokenAuthentication

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        user = s.save()
        return created(
            data=UserSerializer(user).data,
            message="Registro realizado correctamente"
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginByDocumentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        device_id = ser.validated_data["device_id"]
        access = upsert_session(user=user, device_id=device_id, request=request)
        return ok({"access": access, "device_id": device_id}, message="Login exitoso")


class ProfileDataView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = (User.objects
                .select_related("document_type", "city", "district", "position", "dominant_foot", "team")
                .prefetch_related("team_memberships__team")
                .get(pk=request.user.pk))
        return ok(UserSerializer(user).data, message="Perfil")

    def patch(self, request):
        s = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()

        user = (User.objects
                .select_related("document_type", "city", "district", "position", "dominant_foot", "team")
                .prefetch_related("team_memberships__team")
                .get(pk=request.user.pk))
        return ok(UserSerializer(user).data, message="Perfil actualizado")


class ChangePasswordView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["current_password"]):
            return error(message="Contraseña actual incorrecta")
        user.set_password(ser.validated_data["new_password"])
        user.save()
        return ok(message="Contraseña actualizada")


# ---------- LOGOUTS ----------
class LogoutView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Bearer "):
            return Response(
                {"status": "error", "message": "Falta Authorization Bearer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = auth.split(" ", 1)[1]
        payload = logout_by_token(request.user, token)
        return Response(payload, status=status.HTTP_200_OK)


class LogoutAllView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = logout_all(request.user)
        return Response(payload, status=status.HTTP_200_OK)


# ---------- CATÁLOGOS ----------
class RegistrationCatalogView(APIView):
    """
    Devuelve catálogos para la pantalla de registro (excepto distritos, que se carga por city).
    GET /catalogs/registration
    """
    permission_classes = [AllowAny]

    def get(self, request):
        latest_terms = TermsAndConditions.objects.filter(is_active=True, section="register").order_by(
            "-published_at").first()
        return Response({
            "document_types": [{"id": dt.id, "code": dt.code, "name": dt.name}
                               for dt in DocumentType.objects.filter(is_active=True).order_by("id")],
            "cities": [{"id": c.id, "name": c.name} for c in City.objects.filter(is_active=True).order_by("id")],
            "positions": [{"id": p.id, "code": p.code, "name": p.name}
                          for p in FootballPosition.objects.filter(is_active=True).order_by("id")],
            "teams": [
                {"id": t.id, "name": t.name}
                for t in Team.objects.filter(is_active=True).order_by("name")
            ],
            "dominant_feet": [{"id": f.id, "code": f.code, "name": f.name}
                              for f in DominantFoot.objects.filter(is_active=True).order_by("id")],
            "terms": None if not latest_terms else {
                "id": latest_terms.id, "title": latest_terms.title, "body": latest_terms.body
            }
        })


class DistrictsByCityView(APIView):
    """
    GET /catalogs/districts?city_id=#
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            city_id = int(request.query_params.get("city_id"))
        except (TypeError, ValueError):
            return Response({"detail": "city_id es requerido"}, status=400)

        qs = District.objects.filter(city_id=city_id, is_active=True).order_by("id")
        return Response([{"id": d.id, "name": d.name} for d in qs])
