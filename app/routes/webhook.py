"""Webhook verificado para WhatsApp Cloud API."""

import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Empresa, MensajeProcesado
from app.services.conversation_service import process_message
from app.services.whatsapp_service import send_text_message

router = APIRouter(tags=["WhatsApp"])


def verify_signature(raw_body: bytes, signature: str | None) -> bool:
    """Valida que la carga fue firmada por la aplicación de Meta."""
    secret = get_settings().meta_app_secret
    if not secret:
        return get_settings().environment == "development"
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.get("/webhook")
def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    """Completa el handshake requerido al registrar el webhook."""
    settings = get_settings()
    if mode == "subscribe" and token and hmac.compare_digest(
        token, settings.whatsapp_verify_token
    ):
        return Response(content=challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verificación de webhook fallida.")


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Atiende mensajes de texto e ignora estados y tipos no soportados."""
    raw_body = await request.body()
    if not verify_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Firma de Meta inválida.")
    payload = await request.json()
    handled = 0
    ignored = 0

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            empresa = db.scalar(
                select(Empresa).where(
                    Empresa.meta_phone_number_id == str(phone_number_id),
                    Empresa.activa.is_(True),
                )
            )
            if not empresa:
                ignored += len(value.get("messages", []))
                continue
            for message in value.get("messages", []):
                message_id = message.get("id")
                if (
                    not message_id
                    or message.get("type") != "text"
                    or not message.get("text", {}).get("body")
                ):
                    ignored += 1
                    continue
                duplicate = db.scalar(
                    select(MensajeProcesado).where(
                        MensajeProcesado.whatsapp_message_id == message_id
                    )
                )
                if duplicate:
                    ignored += 1
                    continue
                db.add(
                    MensajeProcesado(
                        empresa_id=empresa.id, whatsapp_message_id=message_id
                    )
                )
                result = process_message(
                    db,
                    empresa,
                    message.get("from", ""),
                    message["text"]["body"],
                    notify_external=True,
                )
                try:
                    send_text_message(empresa, message.get("from", ""), result.response)
                except Exception:
                    # Meta reintentará el evento, pero la idempotencia evita duplicados.
                    pass
                handled += 1
    return {"status": "received", "handled": handled, "ignored": ignored}

