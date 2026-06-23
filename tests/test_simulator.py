"""Pruebas de conversación completas sin Meta."""

import json

from sqlalchemy import select

from app.models import Pedido


def simulate(client, company_id, message, number="+593999999999"):
    return client.post(
        "/test/simular-mensaje",
        json={
            "empresa_id": company_id,
            "numero_cliente": number,
            "mensaje": message,
        },
    )


def test_simulator_works_without_external_credentials(
    client, sample_empresa, sample_products
):
    response = simulate(client, sample_empresa["id"], "hola tienes aleja?")
    assert response.status_code == 200
    body = response.json()
    assert body["modo_ia"] == "local"
    assert len(body["productos_encontrados"]) == 3
    assert "Alexa" in body["respuesta_bot"]


def test_context_resolves_third_option(client, sample_empresa, sample_products):
    simulate(client, sample_empresa["id"], "tienes alexa?")
    response = simulate(
        client, sample_empresa["id"], "la 3ra cuanto cuesta el envio"
    )
    body = response.json()
    assert len(body["productos_encontrados"]) == 1
    assert body["productos_encontrados"][0]["nombre"].endswith("3ra Gen")


def test_payment_creates_one_pending_order(
    client, db, sample_empresa, sample_products
):
    simulate(client, sample_empresa["id"], "tienes alexa?")
    simulate(client, sample_empresa["id"], "la tercera")
    first = simulate(client, sample_empresa["id"], "ok me la llevo, como pago?")
    second = simulate(client, sample_empresa["id"], "dame los datos de pago")
    assert first.json()["intencion_detectada"] == "solicitar_pago"
    assert "Banco Demo" in first.json()["respuesta_bot"]
    assert second.status_code == 200
    orders = db.scalars(select(Pedido)).all()
    assert len(orders) == 1
    payload = json.loads(orders[0].productos_json)
    assert payload[0]["nombre"].endswith("3ra Gen")


def test_off_topic_redirects_to_catalog(client, sample_empresa, sample_products):
    response = simulate(client, sample_empresa["id"], "cuéntame un chiste")
    assert response.json()["intencion_detectada"] == "fuera_de_tema"
    assert "catálogo" in response.json()["respuesta_bot"]

