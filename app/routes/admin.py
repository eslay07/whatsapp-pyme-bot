"""Administración de empresas, catálogos e historiales."""

import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_key
from app.models import Conversacion, Empresa, Producto
from app.schemas import (
    ConversacionOut,
    ConversacionWhatsAppTestIn,
    ConversacionWhatsAppTestOut,
    EmpresaCreate,
    EmpresaOut,
    EmpresaUpdate,
    MetaPhoneInfoOut,
    MetaSendTestIn,
    MetaSendTestOut,
    ProductoCreate,
    ProductoEncontrado,
    ProductoOut,
    ProductoUpdate,
)
from app.services.conversation_service import process_message
from app.services.security_service import encrypt_secret
from app.services.whatsapp_service import (
    can_send,
    get_channel_status,
    get_phone_number_info,
    provider_name,
    send_text_message,
)

router = APIRouter(
    prefix="/admin",
    tags=["administración"],
    dependencies=[Depends(require_admin_key)],
)


def _empresa_out(empresa: Empresa) -> EmpresaOut:
    """Construye una respuesta que nunca contiene tokens."""
    meta_configurada = bool(
        empresa.meta_phone_number_id and empresa.meta_access_token_encrypted
    )
    twilio_configurado = bool(
        empresa.twilio_account_sid
        and empresa.twilio_auth_token_encrypted
        and empresa.twilio_from_number
    )
    return EmpresaOut(
        id=empresa.id,
        nombre=empresa.nombre,
        telefono_whatsapp=empresa.telefono_whatsapp,
        telefono_notificacion=empresa.telefono_notificacion,
        numero_cuenta_banco=empresa.numero_cuenta_banco,
        nombre_banco=empresa.nombre_banco,
        nombre_titular_cuenta=empresa.nombre_titular_cuenta,
        mensaje_pago_personalizado=empresa.mensaje_pago_personalizado,
        whatsapp_provider=provider_name(empresa),
        meta_phone_number_id=empresa.meta_phone_number_id,
        twilio_account_sid=empresa.twilio_account_sid,
        twilio_from_number=empresa.twilio_from_number,
        meta_configurada=meta_configurada,
        twilio_configurado=twilio_configurado,
        canal_configurado=can_send(empresa),
        activa=empresa.activa,
        created_at=empresa.created_at,
    )


def _get_empresa(db: Session, empresa_id: int) -> Empresa:
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")
    return empresa


def _get_producto(db: Session, producto_id: int) -> Producto:
    producto = db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return producto


def _safe_meta_error(exc: httpx.HTTPStatusError) -> str:
    """Devuelve un error de Meta entendible sin filtrar credenciales."""
    try:
        data = exc.response.json()
    except ValueError:
        return "Meta rechazó la solicitud."
    error = data.get("error", {}) if isinstance(data, dict) else {}
    message = error.get("message")
    code = error.get("code")
    return f"Meta rechazó la solicitud: {message or 'sin detalle'}" + (
        f" (código {code})." if code else "."
    )


@router.post(
    "/empresas", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED
)
def create_empresa(payload: EmpresaCreate, db: Session = Depends(get_db)) -> EmpresaOut:
    """Registra un tenant y cifra credenciales sensibles si fueron suministradas."""
    data = payload.model_dump(exclude={"meta_access_token", "twilio_auth_token"})
    empresa = Empresa(**data)
    if payload.meta_access_token:
        empresa.meta_access_token_encrypted = encrypt_secret(payload.meta_access_token)
    if payload.twilio_auth_token:
        empresa.twilio_auth_token_encrypted = encrypt_secret(payload.twilio_auth_token)
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return _empresa_out(empresa)


@router.get("/empresas", response_model=list[EmpresaOut])
def list_empresas(db: Session = Depends(get_db)) -> list[EmpresaOut]:
    """Lista empresas sin exponer tokens."""
    rows = db.scalars(select(Empresa).order_by(Empresa.id)).all()
    return [_empresa_out(row) for row in rows]


@router.get("/empresas/{empresa_id}", response_model=EmpresaOut)
def get_empresa(empresa_id: int, db: Session = Depends(get_db)) -> EmpresaOut:
    return _empresa_out(_get_empresa(db, empresa_id))


@router.put("/empresas/{empresa_id}", response_model=EmpresaOut)
def update_empresa(
    empresa_id: int, payload: EmpresaUpdate, db: Session = Depends(get_db)
) -> EmpresaOut:
    """Actualiza solo los campos enviados."""
    empresa = _get_empresa(db, empresa_id)
    data = payload.model_dump(
        exclude_unset=True, exclude={"meta_access_token", "twilio_auth_token"}
    )
    for field, value in data.items():
        setattr(empresa, field, value)
    if payload.meta_access_token is not None:
        empresa.meta_access_token_encrypted = encrypt_secret(payload.meta_access_token)
    if payload.twilio_auth_token is not None:
        empresa.twilio_auth_token_encrypted = encrypt_secret(payload.twilio_auth_token)
    db.commit()
    db.refresh(empresa)
    return _empresa_out(empresa)


@router.get("/empresas/{empresa_id}/canal")
def get_empresa_channel(empresa_id: int, db: Session = Depends(get_db)) -> dict:
    """Devuelve el canal de envío configurado sin secretos."""
    empresa = _get_empresa(db, empresa_id)
    return get_channel_status(empresa)


@router.get(
    "/empresas/{empresa_id}/meta/telefono", response_model=MetaPhoneInfoOut
)
def get_meta_phone_info(
    empresa_id: int, db: Session = Depends(get_db)
) -> MetaPhoneInfoOut:
    """Valida que el token cifrado pueda leer el Phone Number ID configurado."""
    empresa = _get_empresa(db, empresa_id)
    try:
        return MetaPhoneInfoOut(**get_phone_number_info(empresa))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=400, detail=_safe_meta_error(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400,
            detail="No se pudo conectar con Meta. Revisa internet, token y versión de API.",
        ) from exc


@router.post(
    "/empresas/{empresa_id}/meta/probar-envio", response_model=MetaSendTestOut
)
@router.post(
    "/empresas/{empresa_id}/canal/probar-envio", response_model=MetaSendTestOut
)
def send_meta_test_message(
    empresa_id: int, payload: MetaSendTestIn, db: Session = Depends(get_db)
) -> MetaSendTestOut:
    """Envía un texto real usando el canal configurado de la empresa."""
    empresa = _get_empresa(db, empresa_id)
    try:
        sent = send_text_message(empresa, payload.numero_destino, payload.mensaje)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=400, detail=_safe_meta_error(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400,
            detail="No se pudo enviar por WhatsApp. Revisa internet, credenciales y número destino.",
        ) from exc
    if not sent:
        raise HTTPException(
            status_code=400,
            detail="La empresa no tiene un canal de WhatsApp configurado.",
        )
    return MetaSendTestOut(enviado=True, detalle="Mensaje enviado por WhatsApp.")


@router.post(
    "/empresas/{empresa_id}/pruebas/conversacion-whatsapp",
    response_model=ConversacionWhatsAppTestOut,
)
def test_real_conversation(
    empresa_id: int,
    payload: ConversacionWhatsAppTestIn,
    db: Session = Depends(get_db),
) -> ConversacionWhatsAppTestOut:
    """Procesa un mensaje como usuario real y opcionalmente envía la respuesta."""
    empresa = _get_empresa(db, empresa_id)
    if not empresa.activa:
        raise HTTPException(status_code=404, detail="Empresa activa no encontrada.")
    result = process_message(
        db,
        empresa,
        payload.numero_cliente,
        payload.mensaje,
        notify_external=False,
    )
    sent = False
    detail = "La respuesta se generó en modo simulador; no se envió a WhatsApp."
    if payload.enviar_respuesta:
        try:
            sent = send_text_message(empresa, payload.numero_cliente, result.response)
            detail = (
                "Respuesta enviada por WhatsApp."
                if sent
                else "La empresa no tiene Phone Number ID y token Meta configurados."
            )
        except ValueError as exc:
            detail = str(exc)
        except httpx.HTTPStatusError as exc:
            detail = _safe_meta_error(exc)
        except httpx.HTTPError:
            detail = (
                "No se pudo enviar por WhatsApp. La respuesta sí fue generada "
                "y guardada en el historial."
            )
    return ConversacionWhatsAppTestOut(
        respuesta_bot=result.response,
        intencion_detectada=result.intent,
        productos_encontrados=[
            ProductoEncontrado(id=p.id, nombre=p.nombre, precio=p.precio)
            for p in result.products
        ],
        modo_ia=result.mode,
        enviado_whatsapp=sent,
        detalle_envio=detail,
    )


@router.get("/empresas/{empresa_id}/productos", response_model=list[ProductoOut])
def list_productos(empresa_id: int, db: Session = Depends(get_db)) -> list[Producto]:
    _get_empresa(db, empresa_id)
    return list(
        db.scalars(
            select(Producto)
            .where(Producto.empresa_id == empresa_id)
            .order_by(Producto.nombre)
        ).all()
    )


@router.post(
    "/empresas/{empresa_id}/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
)
def create_producto(
    empresa_id: int, payload: ProductoCreate, db: Session = Depends(get_db)
) -> Producto:
    _get_empresa(db, empresa_id)
    producto = Producto(empresa_id=empresa_id, **payload.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.put("/productos/{producto_id}", response_model=ProductoOut)
def update_producto(
    producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)
) -> Producto:
    producto = _get_producto(db, producto_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(producto, field, value)
    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(producto_id: int, db: Session = Depends(get_db)) -> None:
    producto = _get_producto(db, producto_id)
    db.delete(producto)
    db.commit()


@router.get(
    "/conversaciones/{empresa_id}", response_model=list[ConversacionOut]
)
def list_conversations(
    empresa_id: int, db: Session = Depends(get_db)
) -> list[ConversacionOut]:
    _get_empresa(db, empresa_id)
    rows = db.scalars(
        select(Conversacion)
        .where(Conversacion.empresa_id == empresa_id)
        .order_by(Conversacion.updated_at.desc())
    ).all()
    result = []
    for row in rows:
        try:
            history = json.loads(row.historial_json)
        except json.JSONDecodeError:
            history = []
        result.append(
            ConversacionOut(
                id=row.id,
                empresa_id=row.empresa_id,
                numero_cliente=row.numero_cliente,
                historial=history,
                estado=row.estado,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return result
