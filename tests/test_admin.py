"""Pruebas del panel administrativo y aislamiento de tenants."""


def test_admin_rejects_invalid_key(client):
    response = client.get("/admin/empresas/1", headers={"X-Admin-Key": "wrong"})
    assert response.status_code == 401


def test_company_hides_meta_token(client, admin_headers, sample_empresa):
    assert "meta_access_token" not in sample_empresa
    assert sample_empresa["meta_configurada"] is True
    response = client.get(
        f"/admin/empresas/{sample_empresa['id']}", headers=admin_headers
    )
    assert response.status_code == 200
    assert "token-secreto" not in response.text


def test_admin_lists_companies_without_tokens(client, admin_headers, sample_empresa):
    response = client.get("/admin/empresas", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()[0]["id"] == sample_empresa["id"]
    assert "token-secreto" not in response.text


def test_catalog_is_isolated(client, admin_headers, sample_empresa, sample_products):
    second = client.post(
        "/admin/empresas",
        headers=admin_headers,
        json={
            "nombre": "Tienda Dos",
            "telefono_whatsapp": "+593 00 000 0000",
            "telefono_notificacion": "+593 00 000 0000",
            "numero_cuenta_banco": "987",
            "nombre_banco": "Otro Banco",
            "nombre_titular_cuenta": "Tienda Dos",
        },
    ).json()
    first_list = client.get(
        f"/admin/empresas/{sample_empresa['id']}/productos", headers=admin_headers
    )
    second_list = client.get(
        f"/admin/empresas/{second['id']}/productos", headers=admin_headers
    )
    assert len(first_list.json()) == 3
    assert second_list.json() == []


def test_meta_phone_info_uses_stored_token_safely(
    client, admin_headers, sample_empresa, monkeypatch
):
    def fake_phone_info(empresa):
        assert empresa.meta_phone_number_id == "phone-uno"
        return {
            "id": "phone-uno",
            "display_phone_number": "+593 00 000 0000",
            "verified_name": "Tienda Uno",
            "quality_rating": "GREEN",
        }

    monkeypatch.setattr("app.routes.admin.get_phone_number_info", fake_phone_info)

    response = client.get(
        f"/admin/empresas/{sample_empresa['id']}/meta/telefono",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["verified_name"] == "Tienda Uno"
    assert "token-secreto" not in response.text


def test_real_conversation_test_can_send_bot_reply(
    client, admin_headers, sample_empresa, sample_products, monkeypatch
):
    sent_messages = []

    def fake_send_text_message(empresa, recipient, text):
        sent_messages.append((empresa.id, recipient, text))
        return True

    monkeypatch.setattr("app.routes.admin.send_text_message", fake_send_text_message)

    response = client.post(
        f"/admin/empresas/{sample_empresa['id']}/pruebas/conversacion-whatsapp",
        headers=admin_headers,
        json={
            "numero_cliente": "+593 00 000 0000",
            "mensaje": "hola tienes alexa?",
            "enviar_respuesta": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["enviado_whatsapp"] is True
    assert data["productos_encontrados"]
    assert sent_messages[0][1] == "+593 00 000 0000"
    assert "Alexa" in sent_messages[0][2]


def test_twilio_channel_configuration_hides_auth_token(client, admin_headers):
    response = client.post(
        "/admin/empresas",
        headers=admin_headers,
        json={
            "nombre": "Tienda Twilio",
            "telefono_whatsapp": "+593 00 000 0000",
            "telefono_notificacion": "+593 00 000 0000",
            "numero_cuenta_banco": "555",
            "nombre_banco": "Banco Demo",
            "nombre_titular_cuenta": "Tienda Twilio",
            "whatsapp_provider": "twilio",
            "twilio_account_sid": "AC_TEST_ACCOUNT_SID",
            "twilio_auth_token": "twilio-token-secreto",
            "twilio_from_number": "whatsapp:+14155238886",
            "activa": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["whatsapp_provider"] == "twilio"
    assert data["twilio_configurado"] is True
    assert data["canal_configurado"] is True
    assert "twilio-token-secreto" not in response.text


def test_channel_test_send_uses_active_provider(
    client, admin_headers, monkeypatch
):
    created = client.post(
        "/admin/empresas",
        headers=admin_headers,
        json={
            "nombre": "Tienda Twilio",
            "telefono_whatsapp": "+593 00 000 0000",
            "telefono_notificacion": "+593 00 000 0000",
            "numero_cuenta_banco": "555",
            "nombre_banco": "Banco Demo",
            "nombre_titular_cuenta": "Tienda Twilio",
            "whatsapp_provider": "twilio",
            "twilio_account_sid": "AC_TEST_ACCOUNT_SID",
            "twilio_auth_token": "twilio-token-secreto",
            "twilio_from_number": "whatsapp:+14155238886",
            "activa": True,
        },
    ).json()
    sent = []

    def fake_send_text_message(empresa, recipient, text):
        sent.append((empresa.whatsapp_provider, recipient, text))
        return True

    monkeypatch.setattr("app.routes.admin.send_text_message", fake_send_text_message)

    response = client.post(
        f"/admin/empresas/{created['id']}/canal/probar-envio",
        headers=admin_headers,
        json={"numero_destino": "+593 00 000 0000", "mensaje": "Prueba Twilio"},
    )

    assert response.status_code == 200
    assert response.json()["enviado"] is True
    assert sent == [("twilio", "+593 00 000 0000", "Prueba Twilio")]
