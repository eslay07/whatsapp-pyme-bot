"""Alertas al propietario del negocio."""

from app.models import Empresa, Producto
from app.services.whatsapp_service import send_text_message


def notify_owner(
    empresa: Empresa, customer_number: str, products: list[Producto]
) -> bool:
    """Informa una intención de compra usando el número del mismo tenant."""
    detail = "\n".join(f"{p.nombre} - ${p.precio:.2f}" for p in products)
    text = (
        f"⚠️ Cliente {customer_number} quiere comprar:\n"
        f"{detail or 'Producto por confirmar'}\n"
        "Está esperando confirmar el pago."
    )
    return send_text_message(empresa, empresa.telefono_notificacion, text)

