from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.api.models import SessionToken

User = get_user_model()


@receiver(post_save, sender=User)
def revoke_sessions_if_inactive(sender, instance: User, **kwargs):
    # Si el usuario se desactiva desde el admin, borra todas sus sesiones
    if not instance.is_active:
        SessionToken.objects.filter(user=instance).delete()
