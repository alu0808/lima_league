# accounts/serializers.py
import secrets

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction, IntegrityError
from rest_framework import serializers

from accounts.models import (
    DocumentType, City, District, FootballPosition, DominantFoot,
    TermsAndConditions, UserTermsAcceptance
)
from matches.models import Team
from matches.services.memberships import set_current_team, clear_current_team

User = get_user_model()


# --------- Helpers ----------
def validate_document(doc_type_obj, doc_number):
    num = (doc_number or "").strip()
    if doc_type_obj and doc_type_obj.code == "DNI":
        if (not num.isdigit()) or len(num) != 8:
            raise serializers.ValidationError("DNI inválido: debe tener 8 dígitos.")
    return num


# --------- User (lectura) ----------
class UserSerializer(serializers.ModelSerializer):
    document_type = serializers.SlugRelatedField(slug_field="code", read_only=True)
    city = serializers.SlugRelatedField(slug_field="name", read_only=True)
    district = serializers.SlugRelatedField(slug_field="name", read_only=True)
    position = serializers.SlugRelatedField(slug_field="name", read_only=True)
    dominant_foot = serializers.SlugRelatedField(slug_field="name", read_only=True)
    team = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email",
            "first_name", "last_name", "phone", "date_of_birth",
            "document_type", "document_number",
            "city", "district", "photo",
            "position", "dominant_foot", "team",
            "marketing_opt_in"
        )


# --------- Registro (pantalla 1) ----------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    # IDs para selects
    document_type_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.filter(is_active=True), source="document_type"
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_active=True), source="city"
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.filter(is_active=True), source="district"
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=FootballPosition.objects.filter(is_active=True), source="position"
    )
    dominant_foot_id = serializers.PrimaryKeyRelatedField(
        queryset=DominantFoot.objects.filter(is_active=True), source="dominant_foot"
    )

    # TyC
    accept_terms = serializers.BooleanField(write_only=True)
    terms_id = serializers.PrimaryKeyRelatedField(
        queryset=TermsAndConditions.objects.filter(is_active=True, section="register"),
        write_only=True
    )

    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.filter(is_active=True), source="team",
        required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "email", "password",
            "first_name", "last_name",
            "document_type_id", "document_number",
            "date_of_birth", "phone",
            "city_id", "district_id",
            "position_id", "dominant_foot_id",
            "team_id", "photo",
            "marketing_opt_in",
            "accept_terms", "terms_id",
        )

    def _make_username(self, doc_type_obj, doc_number: str) -> str:
        base = f"{doc_type_obj.code}-{(doc_number or '').strip()}".lower()
        candidate = base
        # Evita colisiones en username
        tries = 0
        while User.objects.filter(username__iexact=candidate).exists():
            candidate = f"{base}-{secrets.token_hex(2)}"  # 4 hex chars
            tries += 1
            if tries > 5:
                break
        return candidate

    def validate(self, attrs):
        # Documento
        doc_type = attrs["document_type"]
        attrs["document_number"] = validate_document(doc_type, attrs.get("document_number"))

        # city/district coherentes (opcional pero recomendable)
        city = attrs.get("city")
        district = attrs.get("district")
        if district and city and district.city_id != city.id:
            raise serializers.ValidationError({"district_id": "El distrito no pertenece a la ciudad seleccionada."})

        # email único (más amistoso que esperar IntegrityError)
        if User.objects.filter(email__iexact=attrs.get("email")).exists():
            raise serializers.ValidationError({"email": "Este correo ya está en uso."})

        # TyC obligatorio
        if not attrs.pop("accept_terms", False):
            raise serializers.ValidationError({"accept_terms": "Debes aceptar los Términos y Condiciones."})
        return attrs

    def create(self, validated_data):
        terms = validated_data.pop("terms_id")
        password = validated_data.pop("password")

        # <-- Genera username requerido por AbstractUser
        validated_data["username"] = self._make_username(
            validated_data["document_type"],
            validated_data["document_number"]
        )

        try:
            with transaction.atomic():
                user = User.objects.create_user(password=password, **validated_data)
                request = self.context.get("request")
                UserTermsAcceptance.objects.create(
                    user=user, terms=terms,
                    ip=request.META.get("REMOTE_ADDR") if request else None,
                    user_agent=(request.META.get("HTTP_USER_AGENT", "")[:255] if request else "")
                )

                # NUEVO: si se envió equipo, crear membresía vigente
                team = validated_data.get("team")
                if team:
                    set_current_team(user, team)

                return user

        except IntegrityError:
            # Cae aquí si viola unique de email o (doc_type, doc_number) si lo pusiste como constraint
            raise serializers.ValidationError({"detail": "Documento o email ya registrados."})


# --------- Login ----------
class LoginByDocumentSerializer(serializers.Serializer):
    document_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=DocumentType.objects.all()
    )  # ej. "DNI", "CE", "PAS"
    document_number = serializers.CharField()
    password = serializers.CharField()
    device_id = serializers.RegexField(r"[A-Za-z0-9_\-]{4,64}")

    def validate(self, attrs):
        dt = attrs["document_type"]
        dn = (attrs["document_number"] or "").strip()
        try:
            user = User.objects.get(document_type=dt, document_number=dn)
        except User.DoesNotExist:
            raise serializers.ValidationError("Documento o contraseña inválidos")

        # Autenticamos contra el backend estándar usando el username del usuario
        user_auth = authenticate(username=user.username, password=attrs["password"])
        if not user_auth:
            raise serializers.ValidationError("Documento o contraseña inválidos")

        attrs["user"] = user_auth
        return attrs


# --------- Edición de perfil (pantalla 2) ----------
class ProfileUpdateSerializer(serializers.ModelSerializer):
    # Solo los campos visibles en la pantalla 2 (sin equipo actual)
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=FootballPosition.objects.filter(is_active=True),
        source="position", required=False, allow_null=True
    )
    dominant_foot_id = serializers.PrimaryKeyRelatedField(
        queryset=DominantFoot.objects.filter(is_active=True),
        source="dominant_foot", required=False, allow_null=True
    )
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.filter(is_active=True),
        source="team", required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "first_name", "last_name",
            "phone", "position_id", "dominant_foot_id",
            "team_id", "photo",
            "email",  # si no quieres que cambie el email, bórralo de aquí
        )

    def validate_email(self, value):
        q = User.objects.filter(email__iexact=value)
        if self.instance:
            q = q.exclude(pk=self.instance.pk)
        if q.exists():
            raise serializers.ValidationError("Este correo ya está en uso.")
        return value

    def update(self, instance, validated_data):
        # Extrae el team si llegó (viene desde team_id por source="team")
        new_team = validated_data.pop("team", serializers.empty)

        # Aplica primero el resto de cambios normales (phone, position, etc.)
        instance = super().update(instance, validated_data)

        # Si el front NO envió team_id, no tocamos nada de memberships
        if new_team is serializers.empty:
            return instance

        # Si envió team_id=null -> cerrar vigente y limpiar user.team
        if new_team is None:
            clear_current_team(instance)
            return instance

        # Si envió nuevo equipo distinto al actual -> cerrar vigente y abrir nueva
        if instance.team_id != new_team.id:
            set_current_team(instance, new_team)

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
