from unittest.mock import Mock

import pytest
import requests
from streamlit.testing.v1 import AppTest

from frontend.services.task_service import APIError, TaskService


def test_network_error_is_not_empty_list(monkeypatch):
    monkeypatch.setattr(requests, "request", Mock(side_effect=requests.ConnectionError))
    with pytest.raises(APIError, match="conectar"):
        TaskService("http://localhost:8000").listar("token")


@pytest.mark.parametrize("code", [401, 403, 404, 409, 422, 500])
def test_http_error_is_explicit(monkeypatch, code):
    monkeypatch.setattr(requests, "request", Mock(return_value=Mock(status_code=code)))
    with pytest.raises(APIError) as error:
        TaskService("http://localhost:8000").listar("token")
    assert error.value.status_code == code


def test_invalid_json(monkeypatch):
    monkeypatch.setattr(
        requests,
        "request",
        Mock(return_value=Mock(status_code=200, json=Mock(side_effect=ValueError))),
    )
    with pytest.raises(APIError, match="Resposta inválida"):
        TaskService("http://localhost:8000").listar("token")


def test_login_screen():
    app = AppTest.from_file("frontend/app.py").run()
    assert not app.exception
    assert app.text_input[0].label == "Usuário"


def test_ui_outage_does_not_show_empty_success(monkeypatch):
    monkeypatch.setattr(TaskService, "me", Mock(side_effect=APIError("API indisponível")))
    app = AppTest.from_file("frontend/app.py")
    app.session_state.access_token = "token"
    app.session_state.username = "teste"
    app.run()
    assert not app.exception
    assert app.error[0].value == "API indisponível"
    assert not app.info


def test_ui_expired_session_returns_to_login(monkeypatch):
    monkeypatch.setattr(TaskService, "me", Mock(side_effect=APIError("Expirou", 401)))
    app = AppTest.from_file("frontend/app.py")
    app.session_state.access_token = "token"
    app.session_state.username = "teste"
    app.run()
    assert not app.exception
    assert app.text_input[0].label == "Usuário"
    assert "access_token" not in app.session_state
