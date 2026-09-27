from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlmodel import Session, select

from backend.models import Usuario


def test_task_lifecycle_and_idempotent_completion(client, user_factory):
    headers = user_factory()
    response = client.post(
        "/tarefas", headers=headers, json={"titulo": "  Cortar tecido  ", "prioridade": "Alta"}
    )
    assert response.status_code == 201
    task = response.json()
    assert task["titulo"] == "Cortar tecido"
    assert task["concluido"] is False
    assert client.get("/tarefas", headers=headers).json() == [task]
    for _ in range(2):
        assert (
            client.patch(f"/tarefas/{task['id']}/concluir", headers=headers).json()["concluido"]
            is True
        )
    assert client.delete(f"/tarefas/{task['id']}", headers=headers).status_code == 200
    assert client.get("/tarefas", headers=headers).json() == []


def test_isolation(client, user_factory):
    first, second = user_factory("primeiro"), user_factory("segundo")
    task = client.post("/tarefas", headers=first, json={"titulo": "Privada"}).json()
    assert client.get("/tarefas", headers=second).json() == []
    assert client.patch(f"/tarefas/{task['id']}/concluir", headers=second).status_code == 404
    assert client.delete(f"/tarefas/{task['id']}", headers=second).status_code == 404
    assert len(client.get("/tarefas", headers=first).json()) == 1


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/tarefas"),
        ("post", "/tarefas"),
        ("patch", "/tarefas/1/concluir"),
        ("delete", "/tarefas/1"),
        ("get", "/usuarios/me"),
    ],
)
def test_requires_authentication(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_disabled_user_cannot_login_or_reuse_token(client, user_factory):
    headers = user_factory()
    with Session(client.app.state.engine) as session:
        user = session.exec(select(Usuario)).one()
        user.is_active = False
        session.add(user)
        session.commit()
    assert client.get("/tarefas", headers=headers).status_code == 401
    assert (
        client.post(
            "/token", data={"username": "funcionario", "password": "senha-segura-123"}
        ).status_code
        == 401
    )


def test_no_password_hash_in_response(client, user_factory):
    response = client.get("/usuarios/me", headers=user_factory())
    assert response.status_code == 200
    assert set(response.json()) == {"id", "username", "email", "is_active", "perfil", "setor"}


@pytest.mark.parametrize("field", ["username", "email"])
def test_duplicate_account_is_conflict(client, user_factory, field):
    user_factory()
    data = {"username": "outro", "email": "outro@example.com", "password": "senha-segura-123"}
    data[field] = "funcionario" if field == "username" else "funcionario@example.com"
    assert client.post("/usuarios", json=data).status_code == 409


def test_public_registration_can_be_disabled(client):
    client.app.state.settings.ALLOW_REGISTRATION = False
    assert (
        client.post(
            "/usuarios",
            json={
                "username": "teste",
                "email": "teste@example.com",
                "password": "senha-segura-123",
            },
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"titulo": "   "},
        {"titulo": "x", "prioridade": "Urgente"},
        {"titulo": "x", "usuario_id": 999},
        {"titulo": "x" * 201},
    ],
)
def test_invalid_task_data(client, user_factory, payload):
    assert client.post("/tarefas", headers=user_factory(), json=payload).status_code == 422


@pytest.mark.parametrize(
    "kind", ["expired", "missing_exp", "missing_ver", "wrong_signature", "invalid"]
)
def test_invalid_tokens(client, user_factory, kind):
    user_factory()
    settings = client.app.state.settings
    payload = {
        "sub": "funcionario",
        "ver": 0,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=1),
    }
    if kind == "expired":
        payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    if kind == "missing_ver":
        del payload["ver"]
    if kind == "missing_exp":
        del payload["exp"]
    key = "wrong-key" if kind == "wrong_signature" else settings.SECRET_KEY
    token = "invalid" if kind == "invalid" else jwt.encode(payload, key, algorithm="HS256")
    assert client.get("/tarefas", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_wrong_password(client, user_factory):
    user_factory()
    assert (
        client.post("/token", data={"username": "funcionario", "password": "errada"}).status_code
        == 401
    )


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
