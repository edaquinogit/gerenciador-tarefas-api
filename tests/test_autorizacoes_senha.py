from datetime import timedelta

from sqlmodel import Session

from backend.models.autorizacao_senha import AutorizacaoSenha
from backend.models.ordem import now_utc
from tests.test_admin_ui import app_with_api, labeled
from tests.test_ordens_ui import enter


def autorizar(client, headers, admin):
    pedido = client.post("/usuarios/me/autorizacao-senha", headers=headers)
    assert pedido.status_code == 200
    user = client.get("/usuarios/me", headers=headers).json()
    result = client.post(
        f"/admin/funcionarios/{user['id']}/autorizacao-senha",
        headers=admin,
        json={"permitir": True, "versao": pedido.json()["versao"]},
    )
    assert result.status_code == 200
    return user, result.json()


def test_permission_required_single_use_and_individual(client, setores):
    headers, admin = setores["PRODUCAO"], setores["ADMIN"]
    body = {"current_password": "senha-setor-123", "password": "nova-senha-123"}
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 403
    user, permission = autorizar(client, headers, admin)
    assert (
        client.post("/usuarios/me/senha", headers=setores["SOLICITACAO"], json=body).status_code
        == 403
    )
    assert (
        client.post(
            "/usuarios/me/senha", headers=headers, json={**body, "current_password": "errada"}
        ).status_code
        == 400
    )
    assert (
        client.get("/usuarios/me/autorizacao-senha", headers=headers).json()["status"]
        == "AUTORIZADA"
    )
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 200
    assert client.get("/usuarios/me", headers=headers).status_code == 401
    token = client.post(
        "/token", data={"username": user["username"], "password": body["password"]}
    ).json()["access_token"]
    new_headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.get("/usuarios/me/autorizacao-senha", headers=new_headers).json()["status"]
        == "UTILIZADA"
    )
    assert (
        client.post(
            "/usuarios/me/senha",
            headers=new_headers,
            json={"current_password": body["password"], "password": "outra-senha-123"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/admin/funcionarios/{user['id']}/autorizacao-senha",
            headers=admin,
            json={"permitir": True, "versao": permission["versao"]},
        ).status_code
        == 409
    )


def test_expiry_revoke_and_employee_cannot_approve(client, setores):
    headers, admin = setores["PRODUCAO"], setores["ADMIN"]
    user, permission = autorizar(client, headers, admin)
    path = f"/admin/funcionarios/{user['id']}/autorizacao-senha"
    assert client.get("/admin/autorizacoes-senha", headers=headers).status_code == 403
    assert (
        client.post(
            path, headers=headers, json={"permitir": True, "versao": permission["versao"]}
        ).status_code
        == 403
    )
    body = {"current_password": "senha-setor-123", "password": "nova-senha-123"}
    with Session(client.app.state.engine) as session:
        item = session.get(AutorizacaoSenha, user["id"])
        item.expira_em = now_utc() - timedelta(seconds=1)
        session.add(item)
        session.commit()
    assert (
        client.get("/usuarios/me/autorizacao-senha", headers=headers).json()["status"] == "EXPIRADA"
    )
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 403
    _, permission = autorizar(client, headers, admin)
    assert (
        client.post(
            path, headers=admin, json={"permitir": False, "versao": permission["versao"]}
        ).status_code
        == 200
    )
    assert client.post("/usuarios/me/senha", headers=headers, json=body).status_code == 403
    # Solicitação repetida não cria várias liberações nem muda a versão pendente.
    first = client.post("/usuarios/me/autorizacao-senha", headers=headers).json()
    assert client.post("/usuarios/me/autorizacao-senha", headers=headers).json() == first


def test_admin_reset_revokes_grant_and_admin_can_change_own_password(client, setores):
    user, _ = autorizar(client, setores["PRODUCAO"], setores["ADMIN"])
    assert (
        client.post(
            f"/admin/funcionarios/{user['id']}/senha",
            headers=setores["ADMIN"],
            json={"password": "reset-senha-123"},
        ).status_code
        == 200
    )
    with Session(client.app.state.engine) as session:
        assert session.get(AutorizacaoSenha, user["id"]).status == "REVOGADA"
    assert (
        client.post(
            "/usuarios/me/senha",
            headers=setores["ADMIN"],
            json={"current_password": "senha-admin-123", "password": "nova-admin-123"},
        ).status_code
        == 200
    )


def test_ui_employee_request_admin_approval_and_change(monkeypatch, client, setores):
    employee = app_with_api(monkeypatch, client)
    enter(employee, "producao")
    labeled(employee.radio, "Menu").set_value("Minha conta").run()
    assert not any(e.label == "Nova senha" for e in employee.text_input)
    labeled(employee.button, "Solicitar alteração de senha").click().run()
    assert not employee.exception
    assert any("Aguardando autorização" in e.value for e in employee.info)
    admin = app_with_api(monkeypatch, client)
    admin.session_state.access_token = setores["ADMIN"]["Authorization"].removeprefix("Bearer ")
    admin.run()
    labeled(admin.button, "Permitir troca").click().run()
    assert not admin.exception
    employee.run()
    assert not employee.exception
    labeled(employee.text_input, "Senha atual").set_value("senha-setor-123")
    labeled(employee.text_input, "Nova senha").set_value("nova-senha-123")
    labeled(employee.text_input, "Confirme a nova senha").set_value("nova-senha-123")
    labeled(employee.button, "Alterar minha senha").click().run()
    assert not employee.exception
    assert any(e.label == "Entrar" for e in employee.button)
