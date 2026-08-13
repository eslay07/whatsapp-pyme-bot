"""Fixtures compartidas con una base SQLite aislada."""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_whatsapp_bot.db"
os.environ["ADMIN_SECRET_KEY"] = "test-admin-key"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key"
os.environ["ENVIRONMENT"] = "development"
os.environ["AI_PROVIDER"] = "local"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": "test-admin-key"}


@pytest.fixture
def sample_empresa(client: TestClient, admin_headers: dict[str, str]) -> dict:
    response = client.post(
        "/admin/empresas",
        headers=admin_headers,
        json={
            "nombre": "Tienda Uno",
            "telefono_whatsapp": "+593 00 000 0000",
            "telefono_notificacion": "+593 00 000 0000",
            "numero_cuenta_banco": "123456",
            "nombre_banco": "Banco Demo",
            "nombre_titular_cuenta": "Tienda Uno",
            "mensaje_pago_personalizado": "Paga aquí:",
            "meta_phone_number_id": "phone-uno",
            "meta_access_token": "token-secreto-meta-uno",
            "activa": True,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_products(
    client: TestClient, admin_headers: dict[str, str], sample_empresa: dict
) -> list[dict]:
    products = [
        ("Alexa Echo Dot 1ra Gen", "Asistente Amazon básico", "35.00", "alexa,aleja,echo,primera,1ra"),
        ("Alexa Echo Dot 2da Gen", "Asistente Amazon mejorado", "45.00", "alexa,aleja,echo,segunda,2da"),
        ("Alexa Echo Dot 3ra Gen", "Asistente Amazon premium", "60.00", "alexa,aleja,echo,tercera,3ra"),
    ]
    result = []
    for name, description, price, keywords in products:
        response = client.post(
            f"/admin/empresas/{sample_empresa['id']}/productos",
            headers=admin_headers,
            json={
                "nombre": name,
                "descripcion": description,
                "precio": price,
                "stock": 10,
                "palabras_clave": keywords,
                "categoria": "Asistentes",
                "disponible": True,
            },
        )
        assert response.status_code == 201
        result.append(response.json())
    return result

