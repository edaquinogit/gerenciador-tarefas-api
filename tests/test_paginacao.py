import pytest

from tests.test_admin_ui import app_with_api, labeled
from tests.test_ordens import comando, payload


def painel(monkeypatch, client, headers):
    app = app_with_api(monkeypatch, client)
    app.session_state.access_token = headers["Authorization"].removeprefix("Bearer ")
    app.run()
    labeled(app.button, "Todas as tarefas").click().run()
    assert not app.exception
    return app


def test_orders_page_total_filters_and_legacy_contract(client, admin_headers, user_factory):
    for index in range(22):
        result = client.post(
            "/ordens", headers=admin_headers, json=payload(produto=f"Lençol {index}")
        )
        assert result.status_code == 201
    client.post("/ordens", headers=admin_headers, json=payload(produto="Toalha"))
    page = client.get(
        "/ordens/pagina",
        headers=admin_headers,
        params={"categoria": "ROUPA_DE_CAMA", "offset": 20, "limit": 20},
    )
    assert page.status_code == 200
    assert page.json()["total"] == 22 and len(page.json()["itens"]) == 2
    assert client.get(
        "/ordens/pagina", headers=admin_headers, params={"status": "PRONTO"}
    ).json() == {"total": 0, "itens": []}
    assert (
        client.get("/ordens/pagina", headers=admin_headers, params={"categoria": "BANHO"}).json()[
            "total"
        ]
        == 1
    )
    assert isinstance(client.get("/ordens", headers=admin_headers).json(), list)
    assert client.get("/ordens/pagina").status_code == 401
    assert client.get("/ordens/pagina", headers=user_factory()).status_code == 403


@pytest.mark.parametrize(
    "params",
    [
        {"offset": -1},
        {"limit": 101},
        {"limit": 0},
        {"categoria": "INVALIDA"},
        {"situacao": "INVALIDA"},
    ],
)
def test_order_page_validates_queries(client, admin_headers, params):
    assert client.get("/ordens/pagina", headers=admin_headers, params=params).status_code == 422


def test_panel_recovers_page_when_tasks_disappear(monkeypatch, client, admin_headers):
    for index in range(21):
        client.post("/tarefas", headers=admin_headers, json={"titulo": f"Tarefa {index}"})
    app = painel(monkeypatch, client, admin_headers)
    assert app.button(key="painel_tarefas_pagina_anterior").disabled
    assert not app.button(key="painel_tarefas_pagina_proxima").disabled
    first_ids = set(app.dataframe[0].value["ID"])
    app.button(key="painel_tarefas_pagina_proxima").click().run()
    assert not app.exception
    remaining = int(app.dataframe[0].value.iloc[0]["ID"])
    assert remaining not in first_ids
    assert app.button(key="painel_tarefas_pagina_proxima").disabled
    client.delete(f"/tarefas/{remaining}", headers=admin_headers)
    labeled(app.button, "Atualizar agora").click().run()
    assert not app.exception and not app.error
    assert app.session_state["painel_tarefas_pagina"] == 1
    assert len(app.dataframe[0].value) == 20
    assert any("Página 1 de 1 • 20 registros" in c.value for c in app.caption)
    assert app.button(key="painel_tarefas_pagina_anterior").disabled
    assert app.button(key="painel_tarefas_pagina_proxima").disabled
    labeled(app.selectbox, "Situação das tarefas").select("Concluídas").run()
    assert any("0 registros" in c.value for c in app.caption)
    assert app.button(key="painel_tarefas_pagina_proxima").disabled


def test_orders_recover_after_cancel_and_clamp_stale_page(monkeypatch, client, admin_headers):
    for index in range(21):
        client.post("/ordens", headers=admin_headers, json=payload(produto=f"Capa {index}"))
    app = painel(monkeypatch, client, admin_headers)
    labeled(app.radio, "Menu").set_value("Ordens de produção").run()
    app.button(key="ordens_pagina_proxima").click().run()
    assert app.session_state["ordens_pagina"] == 2
    last = client.get("/ordens", headers=admin_headers, params={"offset": 20}).json()[0]
    response = client.post(
        f"/ordens/{last['id']}/cancelamento",
        headers=admin_headers,
        json=comando(last["versao"], motivo="Teste de paginação"),
    )
    assert response.status_code == 200
    labeled(app.button, "Atualizar fila").click().run()
    assert not app.exception and not app.error
    assert app.session_state["ordens_pagina"] == 1
    assert any("Página 1 de 1 • 20 registros" in c.value for c in app.caption)
    app.session_state["ordens_pagina"] = 999
    labeled(app.button, "Atualizar fila").click().run()
    assert app.session_state["ordens_pagina"] == 1
    assert not any(e.label == "Página" for e in app.number_input)
    assert app.button(key="ordens_pagina_proxima").disabled


def test_urgent_other_category_is_before_normal_bedding(monkeypatch, client, admin_headers):
    for title, priority in (("Lençol normal", "NORMAL"), ("Toalha urgente", "URGENTE")):
        client.post(
            "/ordens", headers=admin_headers, json=payload(produto=title, prioridade=priority)
        )
    app = painel(monkeypatch, client, admin_headers)
    labeled(app.radio, "Menu").set_value("Ordens de produção").run()
    titles = [e.value for e in app.markdown if e.value.startswith("**#")]
    assert "Toalha urgente" in titles[0] and "Lençol normal" in titles[1]
    assert app.subheader[0].value == "Urgentes — 1 nesta página"
    assert len(titles) == 2
