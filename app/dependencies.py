"""Dependencias de seguridad comunes."""

import secrets

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_admin_key(x_admin_key: str = Header(default="")) -> None:
    """Protege las operaciones administrativas con comparación constante."""
    expected = get_settings().admin_secret_key
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave administrativa inválida.",
        )

