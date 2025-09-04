# accounts/authentication.py
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from accounts.api.models import SessionToken

User = get_user_model()


class DeviceTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"  # puede ser str

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b"bearer":
            return None

        if len(auth) != 2:
            raise exceptions.AuthenticationFailed("Authorization header inválido")

        token = auth[1].decode("utf-8")

        try:
            st = SessionToken.objects.select_related("user").get(token=token)
        except SessionToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Sesión cerrada o token inválido")

        if not st.user.is_active:
            raise exceptions.AuthenticationFailed("Usuario inactivo")

        SessionToken.objects.filter(pk=st.pk).update(last_seen=timezone.now())
        return (st.user, st)

    def authenticate_header(self, request):
        return "Bearer"