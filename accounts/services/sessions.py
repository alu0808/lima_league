# accounts/services/sessions.py
import secrets
from typing import Dict, Any, List

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.api.models import SessionToken
from ..utils.datetime import fmt_local
from ..utils.requests import client_ip

User = get_user_model()


def issue_access_token() -> str:
    """Genera un token opaco fuerte (~64 chars)."""
    return secrets.token_urlsafe(48)


def upsert_session(user: User, device_id: str, request) -> str:
    """Crea/actualiza la sesión (una por device_id) y devuelve el token en claro."""
    access = issue_access_token()
    SessionToken.objects.update_or_create(
        user=user, device_id=device_id,
        defaults={
            "document_number": user.document_number,
            "token": access,
            "ip_address": client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
        }
    )
    return access


def serialize_session(st: SessionToken, include_terminated_at: bool = False) -> Dict[str, Any]:
    data = {
        "device_id": st.device_id,
        "created_at": fmt_local(st.created_at),
        "last_seen": fmt_local(st.last_seen),
    }
    if include_terminated_at:
        data["terminated_at"] = fmt_local(timezone.now())
    return data


def logout_by_token(user: User, token: str) -> Dict[str, Any]:
    """Borra la sesión asociada a ese token (si existe) y retorna payload de respuesta uniforme."""
    st = SessionToken.objects.filter(user=user, token=token).first()
    if not st:
        return {
            "status": "error",
            "message": "La sesión ya estaba cerrada o el token es inválido",
            "count": 0,
            "session": None,
        }
    payload = serialize_session(st, include_terminated_at=True)
    st.delete()
    return {
        "status": "success",
        "message": "Sesión terminada",
        "count": 1,
        "session": payload,
    }


def logout_all(user: User) -> Dict[str, Any]:
    """Borra todas las sesiones del usuario y retorna listado de las que se cerraron."""
    sessions: List[SessionToken] = list(SessionToken.objects.filter(user=user))
    if not sessions:
        return {
            "status": "error",
            "message": "No había sesiones activas",
            "count": 0,
            "terminated_sessions": [],
        }
    terminated = [serialize_session(st) for st in sessions]
    SessionToken.objects.filter(user=user).delete()
    return {
        "status": "success",
        "message": f"Se cerraron {len(terminated)} sesiones",
        "count": len(terminated),
        "terminated_sessions": terminated,
    }
