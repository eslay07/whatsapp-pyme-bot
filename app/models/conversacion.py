"""Modelo de historial conversacional."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversacion(Base):
    """Estado e historial de un cliente dentro de una empresa."""

    __tablename__ = "conversaciones"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "numero_cliente", name="uq_conversacion_empresa_cliente"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), index=True
    )
    numero_cliente: Mapped[str] = mapped_column(String(30), index=True)
    historial_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    estado: Mapped[str] = mapped_column(String(30), default="activa", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    empresa = relationship("Empresa", back_populates="conversaciones")

