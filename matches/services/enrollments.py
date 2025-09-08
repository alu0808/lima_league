# matches/services/enrollments.py
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from matches.models import Match, Enrollment, MatchStatus
from stats.api.models import PlayerMatchStat


def active_count(match: Match) -> int:
    return Enrollment.objects.filter(match=match, is_active=True).count()


@transaction.atomic
def join_match(user, match_id: int) -> dict:
    match = Match.objects.select_for_update().get(pk=match_id)

    now = timezone.now() - timedelta(hours=5)
    if match.status != MatchStatus.PUBLISHED:
        raise ValidationError("Match is not open for enrollment.")
    if match.start_at <= now:
        raise ValidationError("Match already started or finished.")

    enr, created = Enrollment.objects.get_or_create(
        match=match, user=user, defaults={"is_active": True}
    )

    # Ya estaba inscrito -> idempotente, garantiza que exista la fila de estadísticas
    if not created and enr.is_active:
        PlayerMatchStat.objects.get_or_create(user=user, match=match)
        return {
            "joined": False,
            "reason": "already_enrolled",
            "available_slots": max(0, match.capacity - active_count(match)),
        }

    # Si estaba cancelado, lo reactivamos luego de verificar cupos
    current = active_count(match)
    if current >= match.capacity:
        raise ValidationError("No slots available.")

    enr.is_active = True
    enr.joined_at = timezone.now() - timedelta(hours=5)
    enr.cancelled_at = None
    enr.save(update_fields=["is_active", "joined_at", "cancelled_at"])

    # crea (o asegura) la fila de stats
    PlayerMatchStat.objects.get_or_create(user=user, match=match)

    return {
        "joined": True,
        "available_slots": max(0, match.capacity - active_count(match)),
    }


@transaction.atomic
def leave_match(user, match_id: int) -> dict:
    match = Match.objects.select_for_update().get(pk=match_id)
    try:
        enr = Enrollment.objects.get(match=match, user=user)
    except Enrollment.DoesNotExist:
        return {"left": False, "reason": "not_enrolled"}

    if not enr.is_active:
        return {"left": False, "reason": "already_cancelled"}

    enr.is_active = False
    enr.cancelled_at = timezone.now() - timedelta(hours=5)
    enr.save(update_fields=["is_active", "cancelled_at"])

    # elimina la fila de stats al darse de baja
    PlayerMatchStat.objects.filter(user=user, match=match).delete()

    return {
        "left": True,
        "available_slots": max(0, match.capacity - active_count(match)),
    }
