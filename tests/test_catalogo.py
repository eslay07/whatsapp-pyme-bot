"""Pruebas de búsqueda tolerante."""

from app.services.catalogo_service import search_products


def test_search_understands_typo(db, sample_products, sample_empresa):
    results = search_products(db, sample_empresa["id"], "buenas tienes aleja?")
    assert len(results) == 3
    assert all("Alexa" in product.nombre for product in results)


def test_search_is_case_and_accent_insensitive(db, sample_products, sample_empresa):
    results = search_products(db, sample_empresa["id"], "ALEXA tercera generación")
    assert results
    assert "3ra" in results[0].nombre


def test_search_returns_empty_for_unknown_product(db, sample_products, sample_empresa):
    assert search_products(db, sample_empresa["id"], "refrigerador industrial") == []

