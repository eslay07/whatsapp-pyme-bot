"""Cliente mínimo de WhatsApp Cloud API."""

import httpx

from app.config import get_settings
from app.models import Empresa
from app.services.security_service import decrypt_secret


def can_send(empresa: Empresa) -> bool:
    """Indica si el tenant tiene credenciales completas."""
    return bool(empresa.meta_phone_number_id and empresa.meta_access_token_encrypted)


def send_text_message(empresa: Empresa, recipient: str, text: str) -> bool:
    """Envía texto plano mediante Graph API y devuelve éxito verificable."""
    if not can_send(empresa):
        return False
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

