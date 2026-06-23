"""Cifrado reversible para credenciales externas."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    """Deriva una clave Fernet estable desde ENCRYPTION_KEY."""
    secret = get_settings().encryption_key
    if not secret:
        secret = get_settings().admin_secret_key
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    """Cifra texto sensible antes de persistirlo."""
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    """Descifra un secreto y reporta una configuración inválida."""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("No se pudo descifrar el token de Meta.") from exc

