from django.conf import settings
from django.db import models

from matches.models import Match


class PlayerMatchStat(models.Model):
    """
    Una fila por (user, match).
    Se crea al inscribirse y se elimina al hacer leave.
    Los campos 'ganó' y 'mvp' pueden quedar sin definir al inicio.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="match_stats"
    )
    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="player_stats"
    )

    goals = models.PositiveIntegerField(default=0)
    is_winner = models.BooleanField(null=True, blank=True)  # True/False/Desconocido
    is_mvp = models.BooleanField(default=False)

    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "match")]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["match"]),
            models.Index(fields=["user", "match"]),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user_id} | {self.match_id} | goals={self.goals}"
