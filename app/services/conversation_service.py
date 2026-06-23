"""Orquestación del ciclo completo de venta."""

import json
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversacion, Empresa, Pedido, Producto
from app.services.ai_service import classify, referenced_ordinal
from app.services.catalogo_service import search_products
from app.services.notificacion_service import notify_owner


@dataclass
class BotResult:
    response: str
    intent: str
    products: list[Producto]
    mode: str


def _history(conversation: Conversacion) -> list[dict]:
    try:
        value = json.loads(conversation.historial_json)
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _get_or_create_conversation(
    db: Session, empresa_id: int, customer_number: str
) -> Conversacion:
    conversation = db.scalar(
        select(Conversacion).where(
            Conversacion.empresa_id == empresa_id,
            Conversacion.numero_cliente == customer_number,
        )
    )
    if conversation is None:
        conversation = Conversacion(
            empresa_id=empresa_id, numero_cliente=customer_number
        )
        db.add(conversation)
        db.flush()
    return conversation


def _products_from_last_context(
    db: Session, history: list[dict], message: str
) -> list[Producto]:
    last_ids: list[int] = []
    for entry in reversed(history):
        if entry.get("role") == "assistant" and entry.get("product_ids"):
            last_ids = entry["product_ids"]
            break
    if not last_ids:
        return []
    ordinal = referenced_ordinal(message)
    selected_ids = (
        [last_ids[ordinal]] if ordinal is not None and ordinal < len(last_ids) else last_ids
    )
    products = db.scalars(select(Producto).where(Producto.id.in_(selected_ids))).all()
    by_id = {product.id: product for product in products}
    return [by_id[item] for item in selected_ids if item in by_id]


def _payment_text(empresa: Empresa) -> str:
    custom = (
        f"{empresa.mensaje_pago_personalizado}\n"
        if empresa.mensaje_pago_personalizado
        else "Puedes realizar una transferencia con estos datos:\n"
    )
    return (
        f"{custom}{empresa.nombre_banco} | Cuenta {empresa.numero_cuenta_banco}\n"
        f"Titular: {empresa.nombre_titular_cuenta}"
    )


def _format_products(products: list[Producto]) -> str:
    lines = [f"{p.nombre} - ${Decimal(p.precio):.2f}" for p in products]
    return "\n".join(lines)


def _create_pending_order(
    db: Session, empresa: Empresa, customer_number: str, products: list[Producto]
) -> Pedido:
    existing = db.scalar(
        select(Pedido)
        .where(
            Pedido.empresa_id == empresa.id,
            Pedido.numero_cliente == customer_number,
            Pedido.estado == "pendiente_pago",
        )
        .order_by(Pedido.created_at.desc())
    )
    payload = [
        {"id": p.id, "nombre": p.nombre, "precio": str(p.precio)} for p in products
    ]
    if existing:
        if payload:
            existing.productos_json = json.dumps(payload, ensure_ascii=False)
        return existing
    order = Pedido(
        empresa_id=empresa.id,
        numero_cliente=customer_number,
        productos_json=json.dumps(payload, ensure_ascii=False),
        estado="pendiente_pago",
    )
    db.add(order)
    return order


def process_message(
    db: Session,
    empresa: Empresa,
    customer_number: str,
    message: str,
    notify_external: bool = False,
) -> BotResult:
    """Procesa, persiste y responde un mensaje dentro del tenant indicado."""
    conversation = _get_or_create_conversation(db, empresa.id, customer_number)
    history = _history(conversation)
    direct_matches = search_products(db, empresa.id, message)
    context_products = _products_from_last_context(db, history, message)
    candidates = direct_matches or context_products
    classification = classify(empresa, message, history, candidates)

    if classification.selected_ids:
        selected_set = set(classification.selected_ids)
        selected = [p for p in candidates if p.id in selected_set]
        products = selected or candidates
    else:
        products = candidates

    if classification.intent == "saludo":
        response = f"¡Hola! Soy el asistente de {empresa.nombre}. ¿Qué producto buscas?"
    elif classification.intent == "fuera_de_tema":
        response = "Puedo ayudarte con los productos de nuestro catálogo. ¿Qué necesitas comprar?"
    elif classification.intent == "ambiguo":
        response = "¿Qué tipo de producto o característica necesitas?"
    elif classification.intent in {"confirmar_compra", "solicitar_pago"}:
        products = context_products or products
        _create_pending_order(db, empresa, customer_number, products)
        conversation.estado = "esperando_pago"
        response = _payment_text(empresa)
        if notify_external:
            try:
                notify_owner(empresa, customer_number, products)
            except Exception:
                # El webhook no debe perder la venta por una alerta externa fallida.
                pass
    elif products:
        response = f"{_format_products(products)}\n¿Cuál te interesa?"
    else:
        response = "No encontré una coincidencia. ¿Qué característica o presupuesto tienes en mente?"

    history.extend(
        [
            {"role": "user", "content": message},
            {
                "role": "assistant",
                "content": response,
                "intent": classification.intent,
                "product_ids": [product.id for product in products],
                "mode": classification.mode,
            },
        ]
    )
    conversation.historial_json = json.dumps(history[-40:], ensure_ascii=False)
    db.commit()
    return BotResult(response, classification.intent, products, classification.mode)
