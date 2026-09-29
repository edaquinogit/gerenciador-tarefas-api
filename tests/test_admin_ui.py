from urllib.parse import urlsplit

import requests
from streamlit.testing.v1 import AppTest


def app_with_api(monkeypatch, client):
    def request(method, url, headers, timeout, **kwargs):
        return client.request(method, urlsplit(url).path, headers=headers, **kwargs)

    monkeypatch.setattr(requests, "request", request)
    return AppTest.from_file("frontend/app.py")


def labeled(elements, label):
    return next(e for e in elements if e.label == label)


def test_admin_ui_creates_and_deactivates_employee(monkeypatch, client, admin_headers):
    app = app_with_api(monkeypatch, client).run()
    labeled(app.text_input, "Usuário").set_value("patrao")
    labeled(app.text_input, "Senha").set_value("senha-admin-123")
    labeled(app.button, "Entrar").click().run()
    assert not app.exception
    assert app.title[0].value == "Funcionários e setores"
    labeled(app.text_input, "Nome de usuário").set_value("costureira")
    labeled(app.text_input, "E-mail").set_value("costureira@example.com")
    labeled(app.selectbox, "Setor").select("PRODUCAO")
    labeled(app.text_input, "Senha inicial").set_value("senha-func-123")
    labeled(app.text_input, "Confirme a senha inicial").set_value("senha-func-123")
    labeled(app.button, "Cadastrar").click().run()
    assert not app.exception
    users = client.get("/admin/funcionarios", headers=admin_headers).json()
    assert len(users) == 1 and users[0]["setor"] == "PRODUCAO"
    labeled(app.checkbox, "Conta ativa").uncheck()
    labeled(app.button, "Salvar alterações").click().run()
    assert not app.exception
    assert client.get("/admin/funcionarios", headers=admin_headers).json()[0]["is_active"] is False


def test_employee_ui_shows_sector_and_no_admin_menu(monkeypatch, client, admin_headers):
    client.post(
        "/admin/funcionarios",
        headers=admin_headers,
        json={
            "username": "operador",
            "email": "operador@example.com",
            "password": "senha-func-123",
            "setor": "COLETA_EMBALAGEM",
        },
    )
    app = app_with_api(monkeypatch, client).run()
    labeled(app.text_input, "Usuário").set_value("operador")
    labeled(app.text_input, "Senha").set_value("senha-func-123")
    labeled(app.button, "Entrar").click().run()
    assert not app.exception
    assert "Funcionários e setores" not in app.radio[0].options
    assert any("Coleta e embalagem" in e.value for e in app.caption)
