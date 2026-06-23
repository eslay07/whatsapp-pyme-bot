"""Pruebas del proveedor OpenAI sin consumir la API."""

from app.services import ai_service


def test_openai_failure_falls_back_to_local(
    monkeypatch, sample_empresa, sample_products, db
):
    from app.models import Empresa, Producto

    empresa = db.get(Empresa, sample_empresa["id"])
    products = [db.get(Producto, item["id"]) for item in sample_products]
    settings = ai_service.get_settings()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "fake-key")

    def fail(*args, **kwargs):
        raise TimeoutError("timeout simulado")

    monkeypatch.setattr(ai_service, "classify_with_openai", fail)
    result = ai_service.classify(empresa, "tienes alexa", [], products)
    assert result.mode == "local"
    assert result.intent == "buscar_producto"


def test_openai_valid_result_is_used(
    monkeypatch, sample_empresa, sample_products, db
):
    from app.models import Empresa, Producto

    empresa = db.get(Empresa, sample_empresa["id"])
    products = [db.get(Producto, item["id"]) for item in sample_products]
    settings = ai_service.get_settings()
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "fake-key")
    expected = ai_service.Classification(
        intent="buscar_producto",
        terms=["alexa"],
        selected_ids=[products[0].id],
        proposed_response="Opción válida",
        mode="openai",
    )
    monkeypatch.setattr(
        ai_service, "classify_with_openai", lambda *args, **kwargs: expected
    )
    assert ai_service.classify(empresa, "alexa", [], products).mode == "openai"

