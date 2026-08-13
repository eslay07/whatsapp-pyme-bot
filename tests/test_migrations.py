"""Comprueba que las migraciones cubren todos los modelos."""

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.database import Base
from app import models  # noqa: F401


def test_migration_head_exists_and_models_are_registered():
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    assert scripts.get_current_head() == "0002_add_whatsapp_providers"
    assert {
        "empresas",
        "productos",
        "conversaciones",
        "pedidos",
        "mensajes_procesados",
    } == set(Base.metadata.tables)
    empresa_columns = set(Base.metadata.tables["empresas"].columns.keys())
    assert {
        "whatsapp_provider",
        "twilio_account_sid",
        "twilio_auth_token_encrypted",
        "twilio_from_number",
    }.issubset(empresa_columns)
