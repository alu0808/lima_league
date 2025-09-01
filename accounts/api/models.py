# accounts/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

# ----- CATÁLOGOS ADMINISTRABLES -----
class DocumentType(models.Model):
    code = models.CharField(max_length=10, unique=True)   # p.ej. DNI, CE, PAS
    name = models.CharField(max_length=100)               # etiqueta visible
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name


class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name


class District(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=120)
    ubigeo = models.CharField(max_length=6, blank=True)   # opcional, si luego cargas RENIEC/INEI
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("city", "name")]
        indexes = [models.Index(fields=["city", "name"])]

    def __str__(self): return f"{self.name} ({self.city.name})"


class FootballPosition(models.Model):
    code = models.CharField(max_length=20, unique=True)   # GK, CB, LB, CM, RW, ST, etc.
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name


class DominantFoot(models.Model):
    code = models.CharField(max_length=10, unique=True)   # R/L/B (diestro/zurdo/ambidiestro)
    name = models.CharField(max_length=30)                # Diestro, Zurdo, Ambidiestro
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name


# ----- TÉRMINOS Y CONDICIONES -----
class TermsAndConditions(models.Model):
    version = models.CharField(max_length=20)  # ej. "2025-08-01"
    title = models.CharField(max_length=200, default="Términos y Condiciones")
    body = models.TextField()                                # o URL si prefieres hosting externo
    is_active = models.BooleanField(default=True)
    section = models.CharField(max_length=100, null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Una sola activa por sección
            models.UniqueConstraint(
                fields=["section", "is_active"],
                condition=Q(is_active=True),
                name="uniq_active_terms_per_section"
            ),
            # No dupliques la misma versión dentro de una sección
            models.UniqueConstraint(
                fields=["section", "version"],
                name="uniq_terms_section_version"
            ),
        ]
        indexes = [
            models.Index(fields=["section", "is_active", "published_at"]),
        ]

    def __str__(self): return f"TyC v{self.section}"


class UserTermsAcceptance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tyc_acceptances")
    terms = models.ForeignKey(TermsAndConditions, on_delete=models.PROTECT)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [("user", "terms")]


# ----- USUARIO + SESIONES -----
class User(AbstractUser):
    email = models.EmailField(unique=True)
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, null=True, blank=True)
    document_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.URLField(max_length=500, blank=True)

    # Dirección / ubicación
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)

    # Fútbol
    position = models.ForeignKey(FootballPosition, on_delete=models.SET_NULL, null=True, blank=True)
    dominant_foot = models.ForeignKey(DominantFoot, on_delete=models.SET_NULL, null=True, blank=True)

    team = models.ForeignKey("matches.Team", on_delete=models.SET_NULL, null=True, blank=True)

    # Marketing / TyC
    marketing_opt_in = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email", "document_type", "document_number"]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document_type", "document_number"],
                name="uniq_user_doc_type_number"
            )
        ]
        indexes = [
            models.Index(fields=["document_number"]),
        ]

    def __str__(self):
        return self.username or self.email


class SessionToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    document_number = models.CharField(max_length=20)
    device_id = models.CharField(max_length=64)
    token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "device_id")]
        indexes = [models.Index(fields=["user", "device_id"]), models.Index(fields=["token"])]

    def __str__(self):
        return f"{self.user_id} | {self.device_id}"