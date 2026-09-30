from tests.test_admin_ui import app_with_api, labeled
from tests.test_ordens import payload


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
    ordem = client.get("/ordens", headers=setores["PRODUCAO"]).json()
    assert len(ordem) == 1
    assert ordem[0]["categoria"] == "OUTROS"
    labeled(app.button, "Sair").click().run()
    enter(app, "producao")
    assert any(e.value.startswith("Outros —") for e in app.subheader)
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


def test_ui_groups_by_category_preserves_urgent_order(monkeypatch, client, setores):
    solicitacao = setores["SOLICITACAO"]
    client.post(
        "/ordens",
        headers=solicitacao,
        json=payload(produto="Lençol casal", especificacao="Branco", prioridade="NORMAL"),
    )
    client.post(
        "/ordens",
        headers=solicitacao,
        json=payload(produto="Fronha avulsa", especificacao="Par", prioridade="URGENTE"),
    )
    client.post(
        "/ordens",
        headers=solicitacao,
        json=payload(produto="Toalha de banho", especificacao="Rosa", prioridade="NORMAL"),
    )
    client.post(
        "/ordens",
        headers=solicitacao,
        json=payload(produto="Cortina voil", especificacao="2m", prioridade="NORMAL"),
    )
    app = app_with_api(monkeypatch, client)
    enter(app, "producao")
    assert not app.exception
    headers = [e.value for e in app.subheader]
    assert headers == ["Roupa de cama — 2 ordens", "Banho — 1 ordem", "Cortinas — 1 ordem"]
    texts = [e.value for e in app.markdown]
    fronha = next(i for i, t in enumerate(texts) if "Fronha avulsa" in t)
    lencol = next(i for i, t in enumerate(texts) if "Lençol casal" in t)
    assert fronha < lencol
    assert any("Prioridade: URGENTE" in e.value for e in app.warning)
    labeled(app.selectbox, "Categoria").select("BANHO").run()
    assert not app.exception
    assert [e.value for e in app.subheader] == ["Banho — 1 ordem"]
    assert any(button.label == "Iniciar corte" for button in app.button)


def test_category_filter_finds_orders_beyond_first_page(monkeypatch, client, setores):
    for index in range(21):
        client.post(
            "/ordens", headers=setores["SOLICITACAO"], json=payload(produto=f"Lençol {index}")
        )
    client.post("/ordens", headers=setores["SOLICITACAO"], json=payload(produto="Toalha final"))
    app = app_with_api(monkeypatch, client)
    enter(app, "producao")
    labeled(app.number_input, "Página").set_value(2).run()
    labeled(app.selectbox, "Categoria").select("BANHO").run()
    assert not app.exception and not app.error
    assert labeled(app.number_input, "Página").value == 1
    assert [e.value for e in app.subheader] == ["Banho — 1 ordem"]
    assert any("Toalha final" in e.value for e in app.markdown)
