"""Clientes de mensajería compatibles con WhatsApp para pruebas y producción."""

import httpx

from app.config import get_settings
from app.models import Empresa
from app.services.security_service import decrypt_secret


def can_send(empresa: Empresa) -> bool:
    """Indica si el tenant tiene credenciales completas."""
    if empresa.whatsapp_provider == "twilio":
        return bool(
            empresa.twilio_account_sid
            and empresa.twilio_auth_token_encrypted
            and empresa.twilio_from_number
        )
    return bool(empresa.meta_phone_number_id and empresa.meta_access_token_encrypted)


def provider_name(empresa: Empresa) -> str:
    """Devuelve el proveedor configurado con un fallback conservador."""
    return empresa.whatsapp_provider or "meta"


def send_text_message(empresa: Empresa, recipient: str, text: str) -> bool:
    """Envía texto plano por el proveedor configurado y devuelve éxito verificable."""
    if not can_send(empresa):
        return False
    if provider_name(empresa) == "twilio":
        return _send_text_message_twilio(empresa, recipient, text)
    return _send_text_message_meta(empresa, recipient, text)


def _send_text_message_meta(empresa: Empresa, recipient: str, text: str) -> bool:
    """Envía texto plano mediante Meta Graph API."""
    settings = get_settings()
    token = decrypt_secret(empresa.meta_access_token_encrypted or "")
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
        f"{empresa.meta_phone_number_id}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    with httpx.Client(timeout=15) as client:
        response = client.post(
            url, headers={"Authorization": f"Bearer {token}"}, json=payload
        )
        response.raise_for_status()
    return True


def _normalize_twilio_whatsapp_number(value: str) -> str:
    """Asegura el formato whatsapp:+593... requerido por Twilio."""
    cleaned = value.strip()
    if cleaned.startswith("whatsapp:"):
        return cleaned
    return f"whatsapp:+{cleaned.lstrip('+')}"


def _send_text_message_twilio(empresa: Empresa, recipient: str, text: str) -> bool:
    """Envía texto usando Twilio Sandbox/Programmable Messaging."""
    account_sid = empresa.twilio_account_sid or ""
    auth_token = decrypt_secret(empresa.twilio_auth_token_encrypted or "")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        "From": _normalize_twilio_whatsapp_number(empresa.twilio_from_number or ""),
        "To": _normalize_twilio_whatsapp_number(recipient),
        "Body": text,
    }
    with httpx.Client(timeout=15) as client:
        response = client.post(url, data=data, auth=(account_sid, auth_token))
        response.raise_for_status()
    return True


def get_phone_number_info(empresa: Empresa) -> dict:
    """Obtiene datos visibles del número configurado en Meta sin exponer tokens."""
    if provider_name(empresa) != "meta":
        raise ValueError("Esta validación aplica solo al proveedor Meta.")
    if not can_send(empresa):
        raise ValueError("La empresa no tiene Phone Number ID y token Meta configurados.")
    settings = get_settings()
    token = decrypt_secret(empresa.meta_access_token_encrypted or "")
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
        f"{empresa.meta_phone_number_id}"
    )
    params = {
        "fields": "id,display_phone_number,verified_name,quality_rating",
    }
    with httpx.Client(timeout=15) as client:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()


def get_channel_status(empresa: Empresa) -> dict:
    """Resume el canal configurado sin revelar credenciales."""
    provider = provider_name(empresa)
    if provider == "twilio":
        return {
            "provider": "twilio",
            "configured": can_send(empresa),
            "from": empresa.twilio_from_number,
            "detail": "Twilio Sandbox/Programmable Messaging",
        }
    return {
        "provider": "meta",
        "configured": can_send(empresa),
        "phone_number_id": empresa.meta_phone_number_id,
        "detail": "Meta WhatsApp Cloud API",
    }
