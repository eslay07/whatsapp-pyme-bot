"""Punto de entrada ASGI."""

from fastapi import FastAPI

from app.config import get_settings
from app.routes import admin, health, test_simulator, webhook

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Bot de ventas multiempresa para WhatsApp con simulador local.",
)
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(admin.router)
app.include_router(test_simulator.router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    """Ofrece enlaces de descubrimiento básicos."""
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }

