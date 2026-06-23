"""Configuración central cargada desde variables de entorno."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores configurables del servicio."""

    app_name: str = "WhatsApp Pyme Bot"
    environment: str = "development"
    database_url: str = "sqlite:///./whatsapp_bot.db"
    admin_secret_key: str = "cambia-esta-clave-administrativa"
    encryption_key: str = ""
    whatsapp_verify_token: str = "elige-un-token-de-verificacion"
    meta_app_secret: str = ""
    whatsapp_api_version: str = "v23.0"
    ai_provider: str = Field(default="local", pattern="^(local|openai)$")
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    openai_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_postgres_url(cls, value: str) -> str:
        """Convierte URLs antiguas de proveedores a la variante de psycopg 3."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia inmutable durante la ejecución."""
    return Settings()

