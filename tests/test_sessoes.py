from datetime import timedelta

import pytest
from sqlmodel import Session, select

from backend.models import Sessao
from backend.services import sessoes

BROWSER = {"Origin": "http://127.0.0.1:8501", "X-Session-Request": "1"}


def browser_login(client, user_factory):
    user_factory()
    login = client.post(
        "/token", data={"username": "funcionario", "password": "senha-segura-123"}
    ).json()
    response = client.post(
        "/sessoes/vincular", headers=BROWSER, json={"code": login["browser_code"]}
    )
    assert response.status_code == 200
    return login, response


def test_cookie_restore_and_logout_revoke_both_credentials(client, user_factory):
    login, claim = browser_login(client, user_factory)
    cookie = claim.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert "path=/sessoes" in cookie
    restored = client.post("/sessoes/restaurar", headers=BROWSER)
    assert restored.status_code == 200
    headers = {"Authorization": f"Bearer {restored.json()['access_token']}"}
    assert client.get("/usuarios/me", headers=headers).status_code == 200
    assert client.post("/sessoes/sair", headers=headers).status_code == 200
    assert client.get("/usuarios/me", headers=headers).status_code == 401
    assert (
        client.get(
            "/usuarios/me", headers={"Authorization": f"Bearer {login['access_token']}"}
        ).status_code
        == 401
    )
    assert client.post("/sessoes/restaurar", headers=BROWSER).status_code == 401


def test_browser_code_single_use_and_hashes_only(client, user_factory):
    login, claim = browser_login(client, user_factory)
    assert (
        client.post(
            "/sessoes/vincular", headers=BROWSER, json={"code": login["browser_code"]}
        ).status_code
        == 401
    )
    with Session(client.app.state.engine) as session:
        record = session.exec(select(Sessao).where(Sessao.cookie_hash.is_not(None))).one()
        assert record.cookie_hash != client.cookies.get(sessoes.COOKIE)
        assert record.codigo_hash is None
    assert claim.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": "https://invasor.example", "X-Session-Request": "1"},
        {"Origin": "http://127.0.0.1:8501"},
    ],
)
def test_browser_endpoints_reject_missing_csrf_or_untrusted_origin(client, headers):
    for path in ("restaurar", "limpar-cookie"):
        assert client.post(f"/sessoes/{path}", headers=headers).status_code == 403


def test_absolute_expiry_and_password_change_invalidate_restore(client, user_factory):
    login, _ = browser_login(client, user_factory)
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    assert (
        client.post(
            "/usuarios/me/senha",
            headers=headers,
            json={"current_password": "senha-segura-123", "password": "senha-nova-123"},
        ).status_code
        == 200
    )
    assert client.post("/sessoes/restaurar", headers=BROWSER).status_code == 401
    assert client.get("/usuarios/me", headers=headers).status_code == 401


def test_session_absolute_expiry_is_not_extended(client, user_factory):
    login, _ = browser_login(client, user_factory)
    before = client.post("/sessoes/restaurar", headers=BROWSER).json()["expires_at"]
    assert client.post("/sessoes/restaurar", headers=BROWSER).json()["expires_at"] == before
    with Session(client.app.state.engine) as session:
        record = session.exec(select(Sessao).where(Sessao.cookie_hash.is_not(None))).one()
        record.expira_em = sessoes.now() - timedelta(seconds=1)
        session.add(record)
        session.commit()
    assert client.post("/sessoes/restaurar", headers=BROWSER).status_code == 401
    assert (
        client.get(
            "/usuarios/me", headers={"Authorization": f"Bearer {login['access_token']}"}
        ).status_code
        == 401
    )


def test_state_is_validated_private_and_cleared_on_logout(client, user_factory):
    first, second = user_factory("primeiro"), user_factory("segundo")
    state = {"pagina_principal": "Ordens de produção", "op_produto": "Toalha", "ordens_pagina": 2}
    assert client.put("/sessoes/estado", headers=first, json={"state": state}).status_code == 200
    assert client.get("/sessoes/estado", headers=first).json()["state"] == state
    assert client.get("/sessoes/estado", headers=second).json()["state"] == {}
    for invalid in ({"access_token": "proibido"}, {"ordens_pagina": 0}, {"op_produto": "x" * 151}):
        assert (
            client.put("/sessoes/estado", headers=first, json={"state": invalid}).status_code == 422
        )
    assert client.post("/sessoes/sair", headers=first).status_code == 200
    assert client.get("/sessoes/estado", headers=first).status_code == 401


def test_cookie_logout_revokes_even_without_a_valid_access_token(client, user_factory):
    login, _ = browser_login(client, user_factory)
    assert client.post("/sessoes/limpar-cookie", headers=BROWSER).status_code == 200
    assert client.post("/sessoes/restaurar", headers=BROWSER).status_code == 401
    assert (
        client.get(
            "/usuarios/me", headers={"Authorization": f"Bearer {login['access_token']}"}
        ).status_code
        == 401
    )


def test_restored_ui_keeps_draft_and_filters_between_views(monkeypatch, client, admin_headers):
    from frontend import session as frontend_session
    from tests.test_admin_ui import app_with_api, labeled

    state = {
        "pagina_principal": "Ordens de produção",
        "op_produto": "Toalha recuperada",
        "ordens_categoria": "BANHO",
    }
    client.put("/sessoes/estado", headers=admin_headers, json={"state": state})
    event = {
        "status": "authenticated",
        "event": "restore-1",
        "state": state,
        "access_token": admin_headers["Authorization"].removeprefix("Bearer "),
        "expires_at": "2099-01-01T12:00:00+00:00",
    }
    monkeypatch.setattr(frontend_session, "browser_session", lambda **kwargs: event)
    app = app_with_api(monkeypatch, client).run()
    assert not app.exception
    assert labeled(app.text_input, "Produto").value == "Toalha recuperada"
    assert labeled(app.selectbox, "Categoria").value == "BANHO"
    labeled(app.text_input, "Produto").set_value("Toalha editada").run()
    labeled(app.radio, "Menu").set_value("Minha conta").run()
    labeled(app.radio, "Menu").set_value("Ordens de produção").run()
    assert not app.exception
    assert labeled(app.text_input, "Produto").value == "Toalha editada"
    assert labeled(app.selectbox, "Categoria").value == "BANHO"
    saved = client.get("/sessoes/estado", headers=admin_headers).json()["state"]
    assert saved["op_produto"] == "Toalha editada"


def test_ui_logout_outage_keeps_session_and_shows_retry(monkeypatch, client, admin_headers):
    from unittest.mock import Mock

    from frontend.services.task_service import APIError, TaskService
    from tests.test_admin_ui import app_with_api, labeled

    app = app_with_api(monkeypatch, client)
    app.session_state.access_token = admin_headers["Authorization"].removeprefix("Bearer ")
    app.run()
    monkeypatch.setattr(TaskService, "sair", Mock(side_effect=APIError("Sem conexão")))
    labeled(app.button, "Sair").click().run()
    assert not app.exception
    assert "access_token" in app.session_state
    assert any("encerrar a sessão" in error.value for error in app.error)
