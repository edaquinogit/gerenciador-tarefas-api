from uuid import uuid4

import pytest


def payload(**changes):
    return {
        "request_id": str(uuid4()),
        "produto": "Capa",
        "especificacao": "Branca 50x70",
        "quantidade": 30,
        "prazo": "2026-10-01T17:00:00-03:00",
        **changes,
    }


def comando(versao, **changes):
    return {"request_id": str(uuid4()), "versao": versao, **changes}


def nova(client, headers):
    response = client.post("/ordens", headers=headers, json=payload())
    assert response.status_code == 201, response.text
    return response.json()


def avancar(client, ordem, headers, status):
    response = client.patch(
        f"/ordens/{ordem['id']}/etapa",
        headers=headers,
        json=comando(ordem["versao"], status=status),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_shared_full_cycle_with_history_and_collection(client, setores):
    ordem = nova(client, setores["SOLICITACAO"])
    ident = ordem["id"]
    assert ordem["solicitante_nome"] == "solicitacao"
    assert ordem["prazo"] == "2026-10-01T20:00:00Z"
    for headers in setores.values():
        assert client.get("/ordens", headers=headers).json()[0]["id"] == ident
    for status in ("CORTANDO", "COSTURANDO", "PRONTO"):
        ordem = avancar(client, ordem, setores["PRODUCAO"], status)
    assert ordem["responsavel_nome"] == "producao" and ordem["pronto_em"]
    data = comando(ordem["versao"])
    result = client.post(f"/ordens/{ident}/coleta", headers=setores["COLETA_EMBALAGEM"], json=data)
    assert result.status_code == 200
    assert result.json()["coletado_nome"] == "coleta_embalagem"
    assert (
        client.post(
            f"/ordens/{ident}/coleta", headers=setores["COLETA_EMBALAGEM"], json=data
        ).status_code
        == 200
    )
    assert client.get("/ordens", headers=setores["SOLICITACAO"]).json() == []
    assert len(client.get("/ordens?situacao=coletadas", headers=setores["SOLICITACAO"]).json()) == 1
    history = client.get(f"/ordens/{ident}/historico", headers=setores["SOLICITACAO"]).json()
    assert [e["acao"] for e in history] == ["CRIACAO", "ETAPA", "ETAPA", "ETAPA", "COLETA"]
    assert [e["versao"] for e in history] == [1, 2, 3, 4, 5]
    assert history[-1]["usuario_nome"] == "coleta_embalagem"


def test_permissions_on_direct_api_calls(client, setores, user_factory):
    for setor in ("PRODUCAO", "COLETA_EMBALAGEM"):
        assert client.post("/ordens", headers=setores[setor], json=payload()).status_code == 403
    ordem = nova(client, setores["SOLICITACAO"])
    path = f"/ordens/{ordem['id']}"
    for setor in ("SOLICITACAO", "COLETA_EMBALAGEM"):
        assert (
            client.patch(
                path + "/etapa", headers=setores[setor], json=comando(1, status="CORTANDO")
            ).status_code
            == 403
        )
    for setor in ("SOLICITACAO", "PRODUCAO"):
        assert (
            client.post(path + "/coleta", headers=setores[setor], json=comando(1)).status_code
            == 403
        )
    for setor in ("SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"):
        assert (
            client.post(
                path + "/cancelamento",
                headers=setores[setor],
                json=comando(1, motivo="Pedido duplicado"),
            ).status_code
            == 403
        )
    sem_setor = user_factory("semsetor")
    for endpoint in ("/ordens", path, path + "/historico"):
        assert client.get(endpoint, headers=sem_setor).status_code == 403
        assert client.get(endpoint).status_code == 401
    assert client.post("/ordens", headers=sem_setor, json=payload()).status_code == 403


def test_invalid_transitions_stale_version_and_idempotency(client, setores):
    ordem = nova(client, setores["SOLICITACAO"])
    path = f"/ordens/{ordem['id']}"
    producao = setores["PRODUCAO"]
    assert (
        client.patch(
            path + "/etapa", headers=producao, json=comando(1, status="PRONTO")
        ).status_code
        == 409
    )
    assert (
        client.post(
            path + "/coleta", headers=setores["COLETA_EMBALAGEM"], json=comando(1)
        ).status_code
        == 409
    )
    data = comando(1, status="CORTANDO")
    for _ in range(2):
        result = client.patch(path + "/etapa", headers=producao, json=data)
        assert result.status_code == 200
        assert result.json()["versao"] == 2
    assert (
        client.patch(
            path + "/etapa", headers=producao, json=comando(1, status="COSTURANDO")
        ).status_code
        == 409
    )
    assert (
        client.patch(
            path + "/etapa", headers=producao, json={**data, "status": "COSTURANDO"}
        ).status_code
        == 409
    )
    assert len(client.get(path + "/historico", headers=producao).json()) == 2


def test_creation_retry_does_not_duplicate(client, setores):
    data = payload()
    first = client.post("/ordens", headers=setores["SOLICITACAO"], json=data).json()
    second = client.post("/ordens", headers=setores["SOLICITACAO"], json=data).json()
    assert first["id"] == second["id"]
    assert len(client.get("/ordens", headers=setores["PRODUCAO"]).json()) == 1
    assert (
        client.post(
            "/ordens", headers=setores["SOLICITACAO"], json={**data, "quantidade": 40}
        ).status_code
        == 409
    )


def test_cancel_preserves_history_and_prevents_changes(client, setores):
    ordem = nova(client, setores["SOLICITACAO"])
    path = f"/ordens/{ordem['id']}"
    data = comando(1, motivo="Solicitação duplicada")
    assert (
        client.post(path + "/cancelamento", headers=setores["ADMIN"], json=data).status_code == 200
    )
    assert (
        client.post(path + "/cancelamento", headers=setores["ADMIN"], json=data).status_code == 200
    )
    assert client.get("/ordens", headers=setores["PRODUCAO"]).json() == []
    assert len(client.get("/ordens?situacao=canceladas", headers=setores["ADMIN"]).json()) == 1
    assert (
        client.patch(
            path + "/etapa", headers=setores["PRODUCAO"], json=comando(2, status="CORTANDO")
        ).status_code
        == 409
    )
    assert client.delete(path, headers=setores["ADMIN"]).status_code == 405
    history = client.get(path + "/historico", headers=setores["ADMIN"]).json()
    assert history[-1]["motivo"] == "Solicitação duplicada"


@pytest.mark.parametrize(
    "changes",
    [
        {"quantidade": 0},
        {"quantidade": 1.5},
        {"produto": " "},
        {"especificacao": " "},
        {"prazo": "2026-10-01T10:00:00"},
        {"solicitante_id": 999},
        {"status": "PRONTO"},
        {"prioridade": "Alta"},
    ],
)
def test_invalid_order_input(client, admin_headers, changes):
    assert client.post("/ordens", headers=admin_headers, json=payload(**changes)).status_code == 422


def test_shared_filters_pagination_and_priority(client, admin_headers):
    normal = nova(client, admin_headers)
    urgent = client.post(
        "/ordens", headers=admin_headers, json=payload(prioridade="URGENTE")
    ).json()
    assert client.get("/ordens?limit=1", headers=admin_headers).json()[0]["id"] == urgent["id"]
    assert (
        client.get("/ordens?limit=1&offset=1", headers=admin_headers).json()[0]["id"]
        == normal["id"]
    )
    assert client.get("/ordens?status=PRONTO", headers=admin_headers).json() == []


def test_reusing_event_key_on_creation_rolls_back(client, admin_headers):
    ordem = nova(client, admin_headers)
    data = comando(1, status="CORTANDO")
    assert (
        client.patch(f"/ordens/{ordem['id']}/etapa", headers=admin_headers, json=data).status_code
        == 200
    )
    assert (
        client.post(
            "/ordens", headers=admin_headers, json=payload(request_id=data["request_id"])
        ).status_code
        == 409
    )
    assert len(client.get("/ordens", headers=admin_headers).json()) == 1
