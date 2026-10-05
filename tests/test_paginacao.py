import pytest

from tests.test_admin_ui import app_with_api, labeled
from tests.test_ordens import comando, payload


def painel(monkeypatch, client, headers):
    app = app_with_api(monkeypatch, client)
    app.session_state.access_token = headers["Authorization"].removeprefix("Bearer ")
    app.run()
    labeled(app.button, "Painel de produção").click().run()
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


def test_panel_recovers_page_when_orders_leave_filter(monkeypatch, client, admin_headers):
    for index in range(21):
        client.post("/ordens", headers=admin_headers, json=payload(produto=f"Lote {index}"))
    app = painel(monkeypatch, client, admin_headers)
    labeled(app.selectbox, "Situação").select("ativas").run()
    app.button(key="painel_ordens_pagina_proxima").click().run()
    assert app.session_state["painel_ordens_pagina"] == 2
    last = client.get("/ordens", headers=admin_headers, params={"offset": 20}).json()[0]
    client.post(
        f"/ordens/{last['id']}/cancelamento",
        headers=admin_headers,
        json=comando(last["versao"], motivo="Teste de paginação"),
    )
    labeled(app.button, "Atualizar agora").click().run()
    assert not app.exception and not app.error
    assert app.session_state["painel_ordens_pagina"] == 1
    assert len([e for e in app.button if str(e.key).startswith("abrir_ordem_")]) == 20
    assert app.button(key="painel_ordens_pagina_proxima").disabled


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
    titles = [e.label for e in app.button if str(e.key).startswith("abrir_ordem_")]
    assert "Toalha urgente" in titles[0] and "Lençol normal" in titles[1]
    assert any("URGENTE" in e.value for e in app.markdown)
    assert len(titles) == 2
