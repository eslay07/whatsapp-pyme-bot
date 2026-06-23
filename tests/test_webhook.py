"""Pruebas de handshake, firma, tenant e idempotencia."""

import hashlib
import hmac
import json

from app.config import get_settings


def webhook_payload(message_id="wamid.1"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": "phone-uno"},
                            "messages": [
                                {
                                    "id": message_id,
                                    "from": "593999999999",
                                    "type": "text",
                                    "text": {"body": "hola tienes alexa?"},
                                }
                            ],
                        },
                    }
                ]
            }
        ],
    }


def test_webhook_verification(client):
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "elige-un-token-de-verificacion",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


def test_webhook_signature_and_duplicate(
    client, monkeypatch, sample_empresa, sample_products
):
    settings = get_settings()
    monkeypatch.setattr(settings, "meta_app_secret", "app-secret")
    monkeypatch.setattr(
        "app.routes.webhook.send_text_message", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        "app.services.conversation_service.notify_owner",
        lambda *args, **kwargs: True,
    )
    raw = json.dumps(webhook_payload(), separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(
        b"app-secret", raw, hashlib.sha256
    ).hexdigest()
    first = client.post(
        "/webhook",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    second = client.post(
        "/webhook",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    assert first.json()["handled"] == 1
    assert second.json()["handled"] == 0
    assert second.json()["ignored"] == 1


def test_webhook_rejects_bad_signature(
    client, monkeypatch, sample_empresa, sample_products
):
    monkeypatch.setattr(get_settings(), "meta_app_secret", "app-secret")
    response = client.post(
        "/webhook",
        json=webhook_payload("wamid.2"),
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 401

