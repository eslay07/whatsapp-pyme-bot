"""Registro de mensajes Meta ya atendidos."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MensajeProcesado(Base):
    """Evita responder dos veces cuando Meta reintenta un webhook."""

    __tablename__ = "mensajes_procesados"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), index=True
    )
    whatsapp_message_id: Mapped[str] = mapped_column(
        String(150), unique=True, index=True
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

