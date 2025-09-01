# matches/services/memberships.py
from django.db import transaction
from django.utils import timezone

from matches.models import TeamMembership

def set_current_team(user, team, start_date=None):
    """
    Cierra la membresía vigente (si existe) y crea una nueva con date_to NULL.
    Sincroniza user.team.
    """
    if start_date is None:
        start_date = timezone.now().date()

    with transaction.atomic():
        # cerrar vigente anterior (si hay)
        TeamMembership.objects.filter(user=user, date_to__isnull=True).update(date_to=start_date)
        # crear nueva
        TeamMembership.objects.create(user=user, team=team, date_from=start_date, date_to=None)
        # sincronizar campo denormalizado
        user.team = team
        user.save(update_fields=["team"])

def clear_current_team(user, end_date=None):
    """
    Cierra la membresía vigente (si existe) y limpia user.team.
    """
    if end_date is None:
        end_date = timezone.now().date()

    with transaction.atomic():
        TeamMembership.objects.filter(user=user, date_to__isnull=True).update(date_to=end_date)
        user.team = None
        user.save(update_fields=["team"])
