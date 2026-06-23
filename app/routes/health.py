"""Comprobación de disponibilidad."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["utilidades"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Verifica que la aplicación y la base de datos respondan."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}

