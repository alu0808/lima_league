# payments/services/mp.py
import mercadopago
from django.conf import settings


def mp_sdk():
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


def _build_back_urls_for_match(match):
    """
    Construye back_urls dinámicos:
    success/failure/pending -> {FRONT_BASE_URL}/{FRONT_MATCH_ROUTE}/{match_identifier}
    """
    base = getattr(settings, "FRONT_BASE_URL", "").rstrip("/")
    route = getattr(settings, "FRONT_MATCH_ROUTE", "/partido").strip("/")

    if not base:
        return None  # sin base, no seteamos back_urls (MP no exige si no pones auto_return)

    base_match_url = f"{base}/{route}/{match.match_identifier}"
    return {
        "success": base_match_url,
        "failure": base_match_url,
        "pending": base_match_url,
    }


def create_preference_for_match(payment, match, user, notify_url: str):
    sdk = mp_sdk()
    ext_ref = str(payment.public_id)

    data = {
        "items": [{
            "title": match.title or f"Partido #{match.id}",
            "quantity": 1,
            "currency_id": payment.currency,  # 'PEN'
            "unit_price": float(payment.amount),
        }],
        "payer": {
            "email": user.email or "noemail@example.com",
            "name": user.first_name or "",
            "surname": user.last_name or "",
        },
        "external_reference": ext_ref
    }

    # back_urls dinámicos por match_identifier
    back_urls = _build_back_urls_for_match(match)
    if back_urls:
        data["back_urls"] = back_urls
        # auto_return requiere back_urls.success definido
        data["auto_return"] = "approved"

    if notify_url:
        data["notification_url"] = notify_url

    # Checkout Pro - Preference
    res = sdk.preference().create(data)
    # Mercado Pago SDK suele devolver {"status": 201, "response": {...}} en éxito
    status_code = res.get("status")
    body = res.get("response", {})

    if status_code not in (200, 201):
        # Devuelve el error tal cual para que lo veas en la API
        raise RuntimeError(f"MercadoPago error {status_code}: {body}")

    # Asegura campos clave
    if not body.get("id") or (not body.get("init_point") and not body.get("sandbox_init_point")):
        raise RuntimeError(f"MercadoPago response missing fields: {body}")

    return body
