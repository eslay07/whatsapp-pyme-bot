"""Simulador local sin dependencias de Meta."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Empresa
from app.schemas import ProductoEncontrado, SimulacionIn, SimulacionOut
from app.services.conversation_service import process_message

router = APIRouter(prefix="/test", tags=["simulador"])


@router.post("/simular-mensaje", response_model=SimulacionOut)
def simulate_message(
    payload: SimulacionIn, db: Session = Depends(get_db)
) -> SimulacionOut:
    """Ejecuta exactamente el mismo motor conversacional, sin enviar mensajes."""
    empresa = db.get(Empresa, payload.empresa_id)
    if not empresa or not empresa.activa:
        raise HTTPException(status_code=404, detail="Empresa activa no encontrada.")
    result = process_message(
        db,
        empresa,
        payload.numero_cliente,
        payload.mensaje,
        notify_external=False,
    )
    return SimulacionOut(
        respuesta_bot=result.response,
        intencion_detectada=result.intent,
        productos_encontrados=[
            ProductoEncontrado(id=p.id, nombre=p.nombre, precio=p.precio)
            for p in result.products
        ],
        modo_ia=result.mode,
    )

