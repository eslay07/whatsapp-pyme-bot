"""Búsqueda tolerante dentro del catálogo aislado por empresa."""

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Producto

STOPWORDS = {
    "a", "al", "algo", "como", "con", "cuanto", "cuesta", "de", "el", "en",
    "es", "hay", "la", "las", "lo", "los", "me", "para", "por", "que",
    "quiero", "tiene", "tienes", "un", "una", "y",
}


def normalize_text(value: str) -> str:
    """Quita tildes, signos y diferencias de mayúsculas."""
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def extract_terms(message: str) -> list[str]:
    """Obtiene términos informativos para búsqueda local."""
    return [
        word
        for word in normalize_text(message).split()
        if len(word) > 1 and word not in STOPWORDS
    ]


@dataclass
class CatalogMatch:
    producto: Producto
    score: float


def search_products(
    db: Session, empresa_id: int, query: str, limit: int = 3
) -> list[Producto]:
    """Puntúa nombre, descripción y sinónimos con coincidencia difusa."""
    products = db.scalars(
        select(Producto).where(
            Producto.empresa_id == empresa_id,
            Producto.disponible.is_(True),
            Producto.stock > 0,
        )
    ).all()
    normalized_query = normalize_text(query)
    terms = extract_terms(query)
    if not normalized_query or not terms:
        return []

    matches: list[CatalogMatch] = []
    for product in products:
        name = normalize_text(product.nombre)
        searchable = normalize_text(
            f"{product.nombre} {product.descripcion} "
            f"{product.palabras_clave} {product.categoria}"
        )
        token_scores = [
            max(fuzz.ratio(term, token) for token in searchable.split())
            for term in terms
        ]
        score = (
            fuzz.token_set_ratio(normalized_query, searchable) * 0.35
            + fuzz.partial_ratio(normalized_query, name) * 0.30
            + (sum(token_scores) / len(token_scores)) * 0.35
        )
        exact_bonus = 18 if any(term in searchable.split() for term in terms) else 0
        score += exact_bonus
        if score >= 57:
            matches.append(CatalogMatch(product, score))

    matches.sort(key=lambda item: (-item.score, item.producto.precio))
    return [item.producto for item in matches[:limit]]


def list_available_products(db: Session, empresa_id: int) -> list[Producto]:
    """Devuelve el catálogo activo para contexto controlado."""
    return list(
        db.scalars(
            select(Producto).where(
                Producto.empresa_id == empresa_id,
                Producto.disponible.is_(True),
                Producto.stock > 0,
            )
        ).all()
    )
