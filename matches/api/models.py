import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from accounts.models import District


class Team(models.Model):
    name = models.CharField(max_length=150, unique=True)
    badge_url = models.URLField(max_length=500, blank=True)
    cover_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return self.name


class TeamMembership(models.Model):
    """
    Historial de pertenencias (user-team) con fechas.
    Al menos un "vigente" por user (date_to = NULL), opcional.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    date_from = models.DateField(default=timezone.now)  # inicio
    date_to = models.DateField(null=True, blank=True)  # fin (NULL = vigente)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_from", "-id"]
        constraints = [
            # Asegura como máximo UNA membresía vigente por usuario
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(date_to__isnull=True),
                name="uniq_user_active_membership"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "date_to"]),
            models.Index(fields=["user", "date_from"]),
        ]

    def __str__(self):
        end = self.date_to.isoformat() if self.date_to else "vigente"
        return f"{self.user_id} -> {self.team.name} [{self.date_from} - {end}]"


class Location(models.Model):
    """Lugar/cancha donde se juega."""
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="locations")
    field_name = models.CharField(max_length=150)  # "Cancha Sport Center"
    address = models.CharField(max_length=255)  # "Av. Pardo 1234"
    maps_url = models.URLField(max_length=500, blank=True)  # link a Google Maps
    photo_url = models.URLField(max_length=500, blank=True)  # portada opcional
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["field_name"]
        unique_together = [("district", "field_name", "address")]

    def __str__(self):
        return f"{self.field_name} - {self.district.name}"


class MatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CANCELLED = "cancelled", "Cancelled"
    FINISHED = "finished", "Finished"


class Match(models.Model):
    """Partido/pichanga."""
    match_identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="matches")

    title = models.CharField(max_length=180, blank=True)  # "Lawn tennis sport"
    image_url = models.URLField(max_length=500, blank=True)
    button_text = models.CharField(max_length=50, default="Quiero ir")

    start_at = models.DateTimeField()  # UTC (timezone-aware)
    duration_minutes = models.PositiveIntegerField(default=90)

    capacity = models.PositiveIntegerField()  # cupos totales
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, default="PEN")  # 'PEN'

    status = models.CharField(max_length=12, choices=MatchStatus.choices, default=MatchStatus.DRAFT)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches_created"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["status", "start_at"]),
        ]

    def __str__(self):
        return self.title or f"Match #{self.pk}"

    @property
    def end_at(self):
        return self.start_at + timezone.timedelta(minutes=self.duration_minutes)


class MatchFAQ(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()

    class Meta:
        ordering = ["id"]


class MatchRecommendation(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="recommendations")
    text = models.CharField(max_length=255)

    class Meta:
        ordering = ["id"]


class Enrollment(models.Model):
    """Inscripción del usuario al partido (una fila por user/party, con 'is_active' para alta/baja)."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="match_enrollments")

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("match", "user")]  # una fila por user/partido
        indexes = [
            models.Index(fields=["match", "is_active"]),
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["match", "joined_at"]),
        ]

        ordering = ["-joined_at"]

    def __str__(self): return f"{self.user_id} -> {self.match_id} ({'active' if self.is_active else 'cancelled'})"
