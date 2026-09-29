from tests.test_admin_ui import app_with_api, labeled


def enter(app, username):
    app.run()
    labeled(app.text_input, "Usuário").set_value(username)
    labeled(app.text_input, "Senha").set_value("senha-setor-123")
    labeled(app.button, "Entrar").click().run()
    assert not app.exception


def test_three_sectors_full_ui_cycle(monkeypatch, client, setores):
    app = app_with_api(monkeypatch, client)
    enter(app, "solicitacao")
    labeled(app.text_input, "Produto").set_value("Capa branca")
    labeled(app.text_input, "Especificação (medida, cor ou tecido)").set_value("50x70")
    labeled(app.number_input, "Quantidade do lote").set_value(30)
    labeled(app.button, "Enviar para produção").click().run()
    assert not app.exception
    assert len(client.get("/ordens", headers=setores["PRODUCAO"]).json()) == 1
    labeled(app.button, "Sair").click().run()
    enter(app, "producao")
    for button in ("Iniciar corte", "Iniciar costura", "Marcar lote pronto"):
        labeled(app.button, button).click().run()
        assert not app.exception
    assert any("disponível para coleta" in e.value for e in app.success)
    labeled(app.button, "Sair").click().run()
    enter(app, "coleta_embalagem")
    labeled(app.checkbox, "Confirmo a retirada de todo o lote").check().run()
    labeled(app.button, "Confirmar coleta").click().run()
    assert not app.exception
    assert len(client.get("/ordens?situacao=coletadas", headers=setores["SOLICITACAO"]).json()) == 1
