import pytest
from pydantic import ValidationError

from backend.schemas.usuario import UsuarioCreate
from tests.test_acessos import DADOS


@pytest.mark.parametrize(
    "value,expected",
    [
        ("(79) 99999-0001", "+5579999990001"),
        ("+55 (79) 99999-0001", "+5579999990001"),
        ("5579999990001", "+5579999990001"),
        ("(79) 3222-0001", "+557932220001"),
        ("55999990001", "+5555999990001"),
    ],
)
def test_phone_normalization(value, expected):
    assert (
        UsuarioCreate(username="teste", telefone=value, password="senha-valida").telefone
        == expected
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "123",
        "999990001",
        "079999990001",
        "+1 79999990001",
        "abc79999990001",
        "(79) 89999-0001",
        "(09) 99999-0001",
        None,
        79999990001,
    ],
)
def test_invalid_phone_is_rejected(value):
    with pytest.raises(ValidationError):
        UsuarioCreate(username="teste", telefone=value, password="senha-valida")


def test_contact_is_required_no_email_and_can_be_shared(client, admin_headers):
    missing = {k: v for k, v in DADOS.items() if k != "telefone"}
    assert (
        client.post("/admin/funcionarios", headers=admin_headers, json=missing).status_code == 422
    )
    assert (
        client.post(
            "/admin/funcionarios", headers=admin_headers, json={**DADOS, "email": "old@example.com"}
        ).status_code
        == 422
    )
    for username in ("pessoa_um", "pessoa_dois"):
        result = client.post(
            "/admin/funcionarios", headers=admin_headers, json={**DADOS, "username": username}
        )
        assert result.status_code == 201
        assert result.json()["telefone"] == "+5579999990001"
        assert "email" not in result.json()


def test_admin_updates_phone_omission_preserves_it(client, admin_headers, user_factory):
    headers = user_factory()
    ident = client.get("/usuarios/me", headers=headers).json()["id"]
    path = f"/admin/funcionarios/{ident}"
    data = {"setor": "PRODUCAO", "is_active": True, "telefone": "(79) 99999-0002"}
    assert client.patch(path, headers=headers, json=data).status_code == 403
    assert (
        client.patch(path, headers=admin_headers, json=data).json()["telefone"] == "+5579999990002"
    )
    del data["telefone"]
    assert (
        client.patch(path, headers=admin_headers, json=data).json()["telefone"] == "+5579999990002"
    )
    for value in (None, "", "inválido"):
        assert (
            client.patch(path, headers=admin_headers, json={**data, "telefone": value}).status_code
            == 422
        )


def test_own_phone_never_changes_other_account_or_privileges(client, user_factory):
    own, other = user_factory("primeiro"), user_factory("segundo")
    path = "/usuarios/me/telefone"
    data = {"telefone": "(79) 3222-0001"}
    assert client.patch(path, json=data).status_code == 401
    assert client.patch(path, headers=own, json={**data, "usuario_id": 2}).status_code == 422
    assert client.patch(path, headers=own, json={**data, "perfil": "ADMIN"}).status_code == 422
    response = client.patch(path, headers=own, json=data)
    assert response.status_code == 200
    assert response.json()["telefone"] == "+557932220001"
    assert response.json()["perfil"] == "FUNCIONARIO"
    assert client.get("/usuarios/me", headers=own).status_code == 200
    assert client.get("/usuarios/me", headers=other).json()["telefone"] == "+5579999990001"
