"""Modelo de pedido pendiente o completado."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Pedido(Base):
    """Intención de compra persistida para seguimiento."""

    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), index=True
    )
    numero_cliente: Mapped[str] = mapped_column(String(30), index=True)
    productos_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    estado: Mapped[str] = mapped_column(
        String(30), default="pendiente_pago", index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    empresa = relationship("Empresa", back_populates="pedidos")

