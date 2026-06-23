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


def test_catalog_is_isolated(client, admin_headers, sample_empresa, sample_products):
    second = client.post(
        "/admin/empresas",
        headers=admin_headers,
        json={
            "nombre": "Tienda Dos",
            "telefono_whatsapp": "+593991111111",
            "telefono_notificacion": "+593992222222",
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

