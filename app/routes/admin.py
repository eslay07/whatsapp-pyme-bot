"""Administración de empresas, catálogos e historiales."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_key
from app.models import Conversacion, Empresa, Producto
from app.schemas import (
    ConversacionOut,
    EmpresaCreate,
    EmpresaOut,
    EmpresaUpdate,
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
)
from app.services.security_service import encrypt_secret

router = APIRouter(
    prefix="/admin",
    tags=["administración"],
    dependencies=[Depends(require_admin_key)],
)


def _empresa_out(empresa: Empresa) -> EmpresaOut:
    """Construye una respuesta que nunca contiene el token."""
    return EmpresaOut(
        id=empresa.id,
        nombre=empresa.nombre,
        telefono_whatsapp=empresa.telefono_whatsapp,
        telefono_notificacion=empresa.telefono_notificacion,
        numero_cuenta_banco=empresa.numero_cuenta_banco,
        nombre_banco=empresa.nombre_banco,
        nombre_titular_cuenta=empresa.nombre_titular_cuenta,
        mensaje_pago_personalizado=empresa.mensaje_pago_personalizado,
        meta_phone_number_id=empresa.meta_phone_number_id,
        meta_configurada=bool(
            empresa.meta_phone_number_id and empresa.meta_access_token_encrypted
        ),
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


@router.post(
    "/empresas", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED
)
def create_empresa(payload: EmpresaCreate, db: Session = Depends(get_db)) -> EmpresaOut:
    """Registra un tenant y cifra su token Meta si fue suministrado."""
    data = payload.model_dump(exclude={"meta_access_token"})
    empresa = Empresa(**data)
    if payload.meta_access_token:
        empresa.meta_access_token_encrypted = encrypt_secret(payload.meta_access_token)
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return _empresa_out(empresa)


@router.get("/empresas/{empresa_id}", response_model=EmpresaOut)
def get_empresa(empresa_id: int, db: Session = Depends(get_db)) -> EmpresaOut:
    return _empresa_out(_get_empresa(db, empresa_id))


@router.put("/empresas/{empresa_id}", response_model=EmpresaOut)
def update_empresa(
    empresa_id: int, payload: EmpresaUpdate, db: Session = Depends(get_db)
) -> EmpresaOut:
    """Actualiza solo los campos enviados."""
    empresa = _get_empresa(db, empresa_id)
    data = payload.model_dump(exclude_unset=True, exclude={"meta_access_token"})
    for field, value in data.items():
        setattr(empresa, field, value)
    if payload.meta_access_token is not None:
        empresa.meta_access_token_encrypted = encrypt_secret(payload.meta_access_token)
    db.commit()
    db.refresh(empresa)
    return _empresa_out(empresa)


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

