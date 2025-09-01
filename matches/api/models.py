from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=150, unique=True)
    badge_url = models.URLField(max_length=500, blank=True)  # Escudo
    cover_url = models.URLField(max_length=500, blank=True)  # Portada
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # fecha de creación

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


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
