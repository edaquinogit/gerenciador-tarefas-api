import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from backend.models import Usuario
from backend.schemas.usuario import UsuarioCreate
from backend.services.usuarios import criar_primeiro_admin

DADOS = {
    "username": "costureira",
    "telefone": "79999990001",
    "password": "senha-func-123",
    "setor": "PRODUCAO",
}


def login(client, username="costureira", password="senha-func-123"):
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_creates_employee_and_assigns_sector(client, admin_headers):
    response = client.post("/admin/funcionarios", headers=admin_headers, json=DADOS)
    assert response.status_code == 201
    assert response.json()["perfil"] == "FUNCIONARIO"
    assert response.json()["setor"] == "PRODUCAO"
    assert "password_hash" not in response.json()
    own = client.get("/usuarios/me", headers=login(client)).json()
    assert own == response.json()
    assert client.get("/admin/funcionarios", headers=admin_headers).json() == [own]


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/admin/funcionarios", None),
        ("post", "/admin/funcionarios", DADOS),
        ("patch", "/admin/funcionarios/1", {"setor": "PRODUCAO", "is_active": False}),
        ("post", "/admin/funcionarios/1/senha", {"password": "outra-senha-123"}),
    ],
)
def test_employee_cannot_administer_even_calling_api_directly(
    client, user_factory, method, path, body
):
    response = client.request(
        method, path, headers=user_factory(), **({"json": body} if body else {})
    )
    assert response.status_code == 403
    assert client.request(method, path, **({"json": body} if body else {})).status_code == 401


@pytest.mark.parametrize(
    "extra",
    [{"perfil": "ADMIN"}, {"is_active": False}, {"token_version": 0}, {"setor": "PRODUCAO"}],
)
def test_public_registration_rejects_privileged_fields(client, extra):
    data = {k: v for k, v in DADOS.items() if k != "setor"}
    assert client.post("/usuarios", json={**data, **extra}).status_code == 422


@pytest.mark.parametrize(
    "data",
    [
        {**DADOS, "perfil": "ADMIN"},
        {**DADOS, "setor": "OUTRO"},
        {k: v for k, v in DADOS.items() if k != "setor"},
    ],
)
def test_admin_creation_validates_sector_and_does_not_promote(client, admin_headers, data):
    assert client.post("/admin/funcionarios", headers=admin_headers, json=data).status_code == 422


def test_disable_reactivate_revokes_old_token_and_preserves_tasks(client, admin_headers):
    user = client.post("/admin/funcionarios", headers=admin_headers, json=DADOS).json()
    old = login(client)
    task = client.post("/tarefas", headers=old, json={"titulo": "Costurar lote"}).json()
    path = f"/admin/funcionarios/{user['id']}"
    assert (
        client.patch(
            path, headers=admin_headers, json={"setor": "PRODUCAO", "is_active": False}
        ).status_code
        == 200
    )
    assert client.get("/tarefas", headers=old).status_code == 401
    assert (
        client.post(
            "/token", data={"username": "costureira", "password": "senha-func-123"}
        ).status_code
        == 401
    )
    assert (
        client.patch(
            path, headers=admin_headers, json={"setor": "COLETA_EMBALAGEM", "is_active": True}
        ).status_code
        == 200
    )
    assert client.get("/tarefas", headers=old).status_code == 401
    new = login(client)
    assert client.get("/tarefas", headers=new).json() == [task]
    assert client.get("/usuarios/me", headers=new).json()["setor"] == "COLETA_EMBALAGEM"


def test_reset_password_revokes_previous_sessions(client, admin_headers):
    user = client.post("/admin/funcionarios", headers=admin_headers, json=DADOS).json()
    old = login(client)
    assert (
        client.post(
            f"/admin/funcionarios/{user['id']}/senha",
            headers=admin_headers,
            json={"password": "nova-senha-123"},
        ).status_code
        == 200
    )
    assert client.get("/usuarios/me", headers=old).status_code == 401
    assert (
        client.post(
            "/token", data={"username": "costureira", "password": "senha-func-123"}
        ).status_code
        == 401
    )
    assert (
        client.get("/usuarios/me", headers=login(client, password="nova-senha-123")).status_code
        == 200
    )


def test_admin_cannot_disable_or_edit_itself_from_employee_endpoints(client, admin_headers):
    own = client.get("/usuarios/me", headers=admin_headers).json()
    assert (
        client.patch(
            f"/admin/funcionarios/{own['id']}",
            headers=admin_headers,
            json={"setor": "PRODUCAO", "is_active": False},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/admin/funcionarios/{own['id']}/senha",
            headers=admin_headers,
            json={"password": "outra-senha-123"},
        ).status_code
        == 403
    )
    assert client.get("/usuarios/me", headers=admin_headers).status_code == 200


def test_change_own_password_requires_current_password(client, user_factory):
    headers = user_factory()
    body = {"current_password": "errada", "password": "nova-senha-123"}
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 400
    body["current_password"] = "senha-segura-123"
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 200
    assert client.get("/usuarios/me", headers=headers).status_code == 401
    assert (
        client.get(
            "/usuarios/me", headers=login(client, "funcionario", "nova-senha-123")
        ).status_code
        == 200
    )


def test_bootstrap_refuses_second_admin(client, admin_headers):
    with Session(client.app.state.engine) as session:
        with pytest.raises(HTTPException) as error:
            criar_primeiro_admin(
                session,
                UsuarioCreate(
                    username="outro", telefone="79999990001", password="senha-valida-123"
                ),
            )
        assert error.value.status_code == 409
        assert len(session.exec(select(Usuario).where(Usuario.perfil == "ADMIN")).all()) == 1


def test_sector_catalog_requires_login(client, user_factory):
    assert client.get("/setores").status_code == 401
    response = client.get("/setores", headers=user_factory())
    assert {s["id"] for s in response.json()} == {"SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"}


def test_employee_cannot_promote_itself_by_update(client, admin_headers):
    user = client.post("/admin/funcionarios", headers=admin_headers, json=DADOS).json()
    path = f"/admin/funcionarios/{user['id']}"
    body = {"setor": "PRODUCAO", "is_active": True, "perfil": "ADMIN"}
    assert client.patch(path, headers=admin_headers, json=body).status_code == 422
    assert client.get("/usuarios/me", headers=login(client)).json()["perfil"] == "FUNCIONARIO"
