# accounts/authentication.py
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from accounts.api.models import SessionToken

User = get_user_model()


class DeviceTokenAuthentication(BaseAuthentication):
    keyword = b"Bearer"

    def authenticate(self, request) -> Optional[Tuple[User, None]]:
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        if auth[0].lower() != self.keyword.lower() or len(auth) != 2:
            return None

        token = auth[1].decode("utf-8")
        try:
            st = SessionToken.objects.select_related("user").get(token=token)
        except SessionToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Sesión cerrada o token inválido")

        if not st.user.is_active:
            raise exceptions.AuthenticationFailed("Usuario inactivo")

        # marcar actividad
        SessionToken.objects.filter(pk=st.pk).update(last_seen=timezone.now())
        return (st.user, None)
