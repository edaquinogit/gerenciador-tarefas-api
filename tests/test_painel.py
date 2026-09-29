from unittest.mock import Mock

import pytest

from frontend.services.task_service import APIError, TaskService
from tests.test_admin_ui import app_with_api, labeled
from tests.test_ordens import avancar, nova


def test_admin_reads_all_tasks_without_changing_ownership(client, admin_headers, user_factory):
    first, second = user_factory("primeiro"), user_factory("segundo")
    one = client.post(
        "/tarefas", headers=first, json={"titulo": "Tarefa da primeira pessoa"}
    ).json()
    two = client.post(
        "/tarefas", headers=second, json={"titulo": "Tarefa da segunda pessoa"}
    ).json()
    client.patch(f"/tarefas/{two['id']}/concluir", headers=second)
    result = client.get("/admin/tarefas", headers=admin_headers).json()
    assert result["total"] == 2
    assert {item["usuario_nome"] for item in result["itens"]} == {"primeiro", "segundo"}
    assert len(client.get("/tarefas", headers=first).json()) == 1
    assert client.get("/tarefas", headers=admin_headers).json() == []
    assert client.patch(f"/tarefas/{one['id']}/concluir", headers=admin_headers).status_code == 404
    assert client.delete(f"/tarefas/{two['id']}", headers=admin_headers).status_code == 404
    for headers, status in (({}, 401), (first, 403)):
        assert client.get("/admin/tarefas", headers=headers).status_code == status
    filtered = client.get(
        "/admin/tarefas", headers=admin_headers, params={"concluido": False}
    ).json()
    assert filtered["total"] == 1 and filtered["itens"][0]["id"] == one["id"]
    page = client.get(
        "/admin/tarefas", headers=admin_headers, params={"offset": 1, "limit": 1}
    ).json()
    assert page["total"] == 2 and page["itens"][0]["id"] == one["id"]
    assert not {"email", "telefone", "password_hash"} & page["itens"][0].keys()


@pytest.mark.parametrize(
    "params", [{"limit": 101}, {"limit": 0}, {"offset": -1}, {"usuario_id": 0}]
)
def test_admin_task_query_limits(client, admin_headers, params):
    assert client.get("/admin/tarefas", headers=admin_headers, params=params).status_code == 422


def test_header_opens_panel_and_refresh_sees_other_sector_changes(monkeypatch, client, setores):
    order = nova(client, setores["SOLICITACAO"])
    task = client.post(
        "/tarefas", headers=setores["PRODUCAO"], json={"titulo": "Separar tecido"}
    ).json()
    app = app_with_api(monkeypatch, client)
    app.session_state.access_token = setores["ADMIN"]["Authorization"].removeprefix("Bearer ")
    app.run()
    labeled(app.button, "Todas as tarefas").click().run()
    assert not app.exception
    assert app.title[0].value == "Todas as tarefas"
    assert app.dataframe[0].value.iloc[0]["Etapa"] == "Pendente"
    assert app.dataframe[1].value.iloc[0]["Pessoa"] == "producao"
    avancar(client, order, setores["PRODUCAO"], "CORTANDO")
    client.patch(f"/tarefas/{task['id']}/concluir", headers=setores["PRODUCAO"])
    labeled(app.button, "Atualizar agora").click().run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]["Etapa"] == "Cortando"
    assert app.dataframe[1].value.iloc[0]["Situação"] == "Concluída"
    for situacao in ("ativas", "coletadas", "canceladas", "todas"):
        labeled(app.selectbox, "Situação das ordens").select(situacao).run()
        assert not app.exception and not app.error
    labeled(app.selectbox, "Etapa da produção").select("CORTANDO").run()
    assert not app.error and len(app.dataframe[0].value) == 1
    # A troca de filtro volta à primeira página para não esconder resultados.
    labeled(app.number_input, "Página de tarefas").set_value(2).run()
    labeled(app.selectbox, "Situação das tarefas").select("Concluídas").run()
    assert labeled(app.number_input, "Página de tarefas").value == 1
    assert len(app.dataframe[1].value) == 1
    monkeypatch.setattr(
        TaskService, "todas_tarefas", Mock(side_effect=APIError("Falha ao consultar tarefas"))
    )
    labeled(app.button, "Atualizar agora").click().run()
    assert not app.exception
    assert any("Falha ao consultar tarefas" in e.value for e in app.error)
    assert not any("Nenhuma tarefa" in e.value for e in app.info)


def test_employee_has_no_global_panel_button(monkeypatch, client, user_factory):
    headers = user_factory()
    app = app_with_api(monkeypatch, client)
    app.session_state.access_token = headers["Authorization"].removeprefix("Bearer ")
    app.run()
    assert not app.exception
    assert "Todas as tarefas" not in app.radio[0].options
    assert all(button.label != "Todas as tarefas" for button in app.button)
