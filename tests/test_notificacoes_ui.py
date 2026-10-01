from unittest.mock import Mock

from frontend.services.task_service import APIError, TaskService
from tests.test_admin_ui import app_with_api, labeled
from tests.test_notificacoes import pronta
from tests.test_ordens_ui import enter


def test_notifications_render_and_read_without_collection(monkeypatch, client, setores):
    ordem = pronta(client, setores)
    app = app_with_api(monkeypatch, client)
    enter(app, "solicitacao")
    assert not app.exception
    assert any("Avisos não lidos: 1" in e.value for e in app.caption)
    assert any("Disponível para coleta" in e.value for e in app.success)
    labeled(app.button, "Marcar como lido").click().run()
    assert not app.exception
    assert any("Avisos não lidos: 0" in e.value for e in app.caption)
    assert (
        client.get(f"/ordens/{ordem['id']}", headers=setores["SOLICITACAO"]).json()["coletado_em"]
        is None
    )
    labeled(app.checkbox, "Incluir avisos lidos").check().run()
    assert any("Lido em" in e.value for e in app.caption)


def test_refresh_keeps_draft_fields_and_does_not_mark_read(monkeypatch, client, setores):
    app = app_with_api(monkeypatch, client)
    enter(app, "solicitacao")
    labeled(app.text_input, "Produto").set_value("Rascunho de capa")
    pronta(client, setores)
    app.run()
    assert not app.exception
    assert labeled(app.text_input, "Produto").value == "Rascunho de capa"
    assert any("Avisos não lidos: 1" in e.value for e in app.caption)
    assert client.get("/notificacoes", headers=setores["SOLICITACAO"]).json()["nao_lidas"] == 1


def test_notice_outage_does_not_claim_empty_inbox(monkeypatch, client, setores):
    app = app_with_api(monkeypatch, client)
    monkeypatch.setattr(
        TaskService, "notificacoes", Mock(side_effect=APIError("Avisos indisponíveis"))
    )
    enter(app, "solicitacao")
    assert not app.exception
    assert any("Avisos indisponíveis" in e.value for e in app.error)
    assert not any("Avisos não lidos: 0" in e.value for e in app.caption)


def test_last_notice_read_clamps_page_and_filter_resets(monkeypatch, client, setores):
    for _ in range(11):
        pronta(client, setores)
    app = app_with_api(monkeypatch, client)
    enter(app, "solicitacao")
    assert app.button(key="avisos_pagina_anterior").disabled
    app.button(key="avisos_pagina_proxima").click().run()
    assert app.session_state["avisos_pagina"] == 2
    assert app.button(key="avisos_pagina_proxima").disabled
    labeled(app.button, "Marcar como lido").click().run()
    assert not app.exception
    assert app.session_state["avisos_pagina"] == 1
    assert app.button(key="avisos_pagina_proxima").disabled
    labeled(app.checkbox, "Incluir avisos lidos").check().run()
    assert app.session_state["avisos_pagina"] == 1
    assert not app.button(key="avisos_pagina_proxima").disabled
    assert (
        client.get(
            "/notificacoes", headers=setores["SOLICITACAO"], params={"somente_nao_lidas": False}
        ).json()["total"]
        == 11
    )
