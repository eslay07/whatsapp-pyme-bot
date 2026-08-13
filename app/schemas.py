"""Contratos públicos de entrada y salida de la API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EmpresaBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    telefono_whatsapp: str = Field(min_length=5, max_length=30)
    telefono_notificacion: str = Field(min_length=5, max_length=30)
    numero_cuenta_banco: str = Field(min_length=2, max_length=100)
    nombre_banco: str = Field(min_length=2, max_length=100)
    nombre_titular_cuenta: str = Field(min_length=2, max_length=150)
    mensaje_pago_personalizado: str | None = None
    whatsapp_provider: Literal["meta", "twilio"] = "meta"
    meta_phone_number_id: str | None = Field(default=None, max_length=100)
    twilio_account_sid: str | None = Field(default=None, max_length=100)
    twilio_from_number: str | None = Field(default=None, max_length=50)
    activa: bool = True


class EmpresaCreate(EmpresaBase):
    meta_access_token: str | None = Field(default=None, min_length=10)
    twilio_auth_token: str | None = Field(default=None, min_length=10)


class EmpresaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    telefono_whatsapp: str | None = Field(default=None, min_length=5, max_length=30)
    telefono_notificacion: str | None = Field(
        default=None, min_length=5, max_length=30
    )
    numero_cuenta_banco: str | None = None
    nombre_banco: str | None = None
    nombre_titular_cuenta: str | None = None
    mensaje_pago_personalizado: str | None = None
    whatsapp_provider: Literal["meta", "twilio"] | None = None
    meta_phone_number_id: str | None = None
    meta_access_token: str | None = Field(default=None, min_length=10)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = Field(default=None, min_length=10)
    twilio_from_number: str | None = None
    activa: bool | None = None


class EmpresaOut(EmpresaBase):
    id: int
    meta_configurada: bool
    twilio_configurado: bool
    canal_configurado: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=200)
    descripcion: str = Field(min_length=2)
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    palabras_clave: str = ""
    categoria: str = Field(min_length=2, max_length=100)
    disponible: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    palabras_clave: str | None = None
    categoria: str | None = None
    disponible: bool | None = None


class ProductoOut(ProductoBase):
    id: int
    empresa_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SimulacionIn(BaseModel):
    empresa_id: int
    numero_cliente: str = Field(min_length=5, max_length=30)
    mensaje: str = Field(min_length=1, max_length=2000)


class ProductoEncontrado(BaseModel):
    id: int
    nombre: str
    precio: Decimal


class SimulacionOut(BaseModel):
    respuesta_bot: str
    intencion_detectada: str
    productos_encontrados: list[ProductoEncontrado]
    modo_ia: Literal["local", "openai"]


class MetaSendTestIn(BaseModel):
    numero_destino: str = Field(min_length=5, max_length=30)
    mensaje: str = Field(min_length=1, max_length=2000)


class MetaSendTestOut(BaseModel):
    enviado: bool
    detalle: str


class MetaPhoneInfoOut(BaseModel):
    id: str
    display_phone_number: str | None = None
    verified_name: str | None = None
    quality_rating: str | None = None


class ConversacionWhatsAppTestIn(BaseModel):
    numero_cliente: str = Field(min_length=5, max_length=30)
    mensaje: str = Field(min_length=1, max_length=2000)
    enviar_respuesta: bool = True


class ConversacionWhatsAppTestOut(SimulacionOut):
    enviado_whatsapp: bool
    detalle_envio: str


class ConversacionOut(BaseModel):
    id: int
    empresa_id: int
    numero_cliente: str
    historial: list[dict]
    estado: str
    created_at: datetime
    updated_at: datetime
