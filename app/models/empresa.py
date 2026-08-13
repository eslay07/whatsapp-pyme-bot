"""Modelo de empresa o tenant."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Empresa(Base):
    """Configuración independiente de cada comercio."""

    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono_whatsapp: Mapped[str] = mapped_column(String(30), nullable=False)
    telefono_notificacion: Mapped[str] = mapped_column(String(30), nullable=False)
    numero_cuenta_banco: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_banco: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_titular_cuenta: Mapped[str] = mapped_column(String(150), nullable=False)
    mensaje_pago_personalizado: Mapped[str | None] = mapped_column(Text)
    whatsapp_provider: Mapped[str] = mapped_column(
        String(30), default="meta", nullable=False
    )
    meta_phone_number_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True
    )
    meta_access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    twilio_account_sid: Mapped[str | None] = mapped_column(String(100))
    twilio_auth_token_encrypted: Mapped[str | None] = mapped_column(Text)
    twilio_from_number: Mapped[str | None] = mapped_column(String(50))
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    productos = relationship(
        "Producto", back_populates="empresa", cascade="all, delete-orphan"
    )
    conversaciones = relationship(
        "Conversacion", back_populates="empresa", cascade="all, delete-orphan"
    )
    pedidos = relationship(
        "Pedido", back_populates="empresa", cascade="all, delete-orphan"
    )
