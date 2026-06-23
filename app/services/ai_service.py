"""Clasificación local y mejora opcional con OpenAI."""

import json
import re
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import Empresa, Producto
from app.prompts.intent_prompt import INTENT_PROMPT
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.services.catalogo_service import extract_terms, normalize_text

Intent = Literal[
    "buscar_producto",
    "confirmar_compra",
    "solicitar_pago",
    "saludo",
    "fuera_de_tema",
    "ambiguo",
]


class AIClassification(BaseModel):
    """Esquema estricto exigido al modelo."""

    intent: Intent
    search_terms: list[str] = Field(default_factory=list, max_length=8)
    selected_product_ids: list[int] = Field(default_factory=list, max_length=3)
    proposed_response: str = Field(max_length=700)


@dataclass
class Classification:
    intent: Intent
    terms: list[str]
    selected_ids: list[int]
    proposed_response: str = ""
    mode: Literal["local", "openai"] = "local"


PAYMENT_WORDS = (
    "como pago", "cómo pago", "datos de pago", "cuenta", "transferir",
    "transferencia", "forma de pago",
)
BUY_WORDS = (
    "me lo llevo", "me la llevo", "quiero comprar", "lo compro", "la compro",
    "voy a comprar", "dame ese", "dame esa", "confirmo",
)
GREETINGS = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}
OFF_TOPIC = (
    "clima", "presidente", "futbol", "fútbol", "chiste", "tarea",
)


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    """Busca frases completas para evitar casos como cuenta/cuéntame."""
    return any(
        re.search(rf"\b{re.escape(normalize_text(phrase))}\b", text)
        for phrase in phrases
    )


def classify_local(message: str, candidates: list[Producto]) -> Classification:
    """Clasificador determinista disponible sin servicios externos."""
    normalized = normalize_text(message)
    if _contains_phrase(normalized, PAYMENT_WORDS):
        intent: Intent = "solicitar_pago"
    elif _contains_phrase(normalized, BUY_WORDS):
        intent = "confirmar_compra"
    elif not candidates and (normalized in GREETINGS or (
        any(normalized.startswith(greeting) for greeting in GREETINGS)
        and len(normalized.split()) <= 3
    )):
        intent = "saludo"
    elif _contains_phrase(normalized, OFF_TOPIC):
        intent = "fuera_de_tema"
    elif not extract_terms(message):
        intent = "ambiguo"
    else:
        intent = "buscar_producto"
    return Classification(
        intent=intent,
        terms=extract_terms(message),
        selected_ids=[product.id for product in candidates],
    )


def classify_with_openai(
    empresa: Empresa,
    message: str,
    history: list[dict],
    candidates: list[Producto],
) -> Classification:
    """Usa Responses API; cualquier fallo permite volver al motor local."""
    settings = get_settings()
    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
        max_retries=1,
    )
    candidate_data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": str(p.precio),
            "stock": p.stock,
        }
        for p in candidates
    ]
    response = client.responses.parse(
        model=settings.openai_model,
        instructions=SYSTEM_PROMPT.format(nombre_empresa=empresa.nombre),
        input=[
            {
                "role": "user",
                "content": (
                    f"{INTENT_PROMPT}\n"
                    f"HISTORIAL: {json.dumps(history[-8:], ensure_ascii=False)}\n"
                    f"PRODUCTOS_CANDIDATOS: "
                    f"{json.dumps(candidate_data, ensure_ascii=False)}\n"
                    f"ÚLTIMO_MENSAJE: {message}"
                ),
            }
        ],
        text_format=AIClassification,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise ValueError("OpenAI no devolvió una clasificación válida.")
    valid_ids = {p.id for p in candidates}
    selected = [item for item in parsed.selected_product_ids if item in valid_ids]
    return Classification(
        intent=parsed.intent,
        terms=parsed.search_terms,
        selected_ids=selected,
        proposed_response=parsed.proposed_response.strip(),
        mode="openai",
    )


def classify(
    empresa: Empresa,
    message: str,
    history: list[dict],
    candidates: list[Producto],
) -> Classification:
    """Selecciona proveedor y aplica fallback silencioso y seguro."""
    settings = get_settings()
    local = classify_local(message, candidates)
    if settings.ai_provider != "openai" or not settings.openai_api_key:
        return local
    try:
        return classify_with_openai(empresa, message, history, candidates)
    except Exception:
        return local


def referenced_ordinal(message: str) -> int | None:
    """Convierte referencias como 'la tercera' o '3ra' a índice cero."""
    normalized = normalize_text(message)
    variants = {
        0: ("primera", "primero", "1ra", "1era", "1"),
        1: ("segunda", "segundo", "2da", "2"),
        2: ("tercera", "tercero", "3ra", "3era", "3"),
    }
    for index, words in variants.items():
        if any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in words):
            return index
    return None
