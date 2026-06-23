"""Comprueba que la migración inicial cubre todos los modelos."""

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.database import Base
from app import models  # noqa: F401


def test_migration_head_exists_and_models_are_registered():
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    assert scripts.get_current_head() == "0001_initial"
    assert {
        "empresas",
        "productos",
        "conversaciones",
        "pedidos",
        "mensajes_procesados",
    } == set(Base.metadata.tables)

