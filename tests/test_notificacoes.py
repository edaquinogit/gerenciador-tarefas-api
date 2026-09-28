import pytest
from sqlalchemy import event
from sqlmodel import Session, select

from backend.models.notificacao import Notificacao
from backend.models.ordem import EventoOrdem, Ordem
from tests.test_ordens import avancar, comando, nova


def pronta(client, setores):
    ordem = nova(client, setores["SOLICITACAO"])
    for status in ("CORTANDO", "COSTURANDO", "PRONTO"):
        ordem = avancar(client, ordem, setores["PRODUCAO"], status)
    return ordem


def caixa(client, headers, **params):
    response = client.get("/notificacoes", headers=headers, params=params)
    assert response.status_code == 200
    return response.json()


def test_ready_notifies_requester_admin_and_collection_once(client, setores, user_factory):
    outros = user_factory("outro_solicitante")
    # Cadastro inativo no setor de coleta não recebe avisos.
    inactive = client.post(
        "/admin/funcionarios",
        headers=setores["ADMIN"],
        json={
            "username": "inativo",
            "email": "inativo@example.com",
            "password": "senha-inativo-123",
            "setor": "COLETA_EMBALAGEM",
        },
    ).json()
    client.patch(
        f"/admin/funcionarios/{inactive['id']}",
        headers=setores["ADMIN"],
        json={"setor": "COLETA_EMBALAGEM", "is_active": False},
    )
    ordem = nova(client, setores["SOLICITACAO"])
    assert caixa(client, setores["ADMIN"])["nao_lidas"] == 0
    for status in ("CORTANDO", "COSTURANDO"):
        ordem = avancar(client, ordem, setores["PRODUCAO"], status)
    data = comando(ordem["versao"], status="PRONTO")
    for _ in range(2):
        assert (
            client.patch(
                f"/ordens/{ordem['id']}/etapa", headers=setores["PRODUCAO"], json=data
            ).status_code
            == 200
        )
    for setor in ("SOLICITACAO", "ADMIN", "COLETA_EMBALAGEM"):
        resumo = caixa(client, setores[setor])
        assert resumo["nao_lidas"] == 1
        assert resumo["itens"][0]["ordem_id"] == ordem["id"]
        assert resumo["itens"][0]["situacao"] == "AGUARDANDO_COLETA"
        assert resumo["itens"][0]["criado_em"].endswith("Z")
    assert caixa(client, setores["PRODUCAO"])["nao_lidas"] == 0
    assert client.get("/notificacoes", headers=outros).status_code == 403
    with Session(client.app.state.engine) as session:
        assert len(session.exec(select(Notificacao)).all()) == 3
        assert not session.exec(
            select(Notificacao).where(Notificacao.usuario_id == inactive["id"])
        ).all()


def test_read_is_individual_persistent_idempotent_and_does_not_collect(client, setores):
    ordem = pronta(client, setores)
    notice = caixa(client, setores["SOLICITACAO"])["itens"][0]
    assert (
        client.patch(f"/notificacoes/{notice['id']}/lida", headers=setores["ADMIN"]).status_code
        == 404
    )
    assert (
        client.patch(
            f"/notificacoes/{notice['id']}/lida", headers=setores["SOLICITACAO"]
        ).status_code
        == 200
    )
    saved = caixa(client, setores["SOLICITACAO"], somente_nao_lidas=False)["itens"][0]
    assert saved["lida_em"]
    assert (
        client.patch(
            f"/notificacoes/{notice['id']}/lida", headers=setores["SOLICITACAO"]
        ).status_code
        == 200
    )
    assert (
        caixa(client, setores["SOLICITACAO"], somente_nao_lidas=False)["itens"][0]["lida_em"]
        == saved["lida_em"]
    )
    assert caixa(client, setores["SOLICITACAO"])["nao_lidas"] == 0
    assert caixa(client, setores["COLETA_EMBALAGEM"])["nao_lidas"] == 1
    response = client.get(f"/ordens/{ordem['id']}", headers=setores["SOLICITACAO"]).json()
    assert response["coletado_em"] is None and response["versao"] == ordem["versao"]
    token = client.post(
        "/token", data={"username": "solicitacao", "password": "senha-setor-123"}
    ).json()["access_token"]
    assert (
        caixa(client, {"Authorization": f"Bearer {token}"}, somente_nao_lidas=False)["itens"][0][
            "lida_em"
        ]
        == saved["lida_em"]
    )


@pytest.mark.parametrize("acao,expected", [("coleta", "COLETADA"), ("cancelamento", "CANCELADA")])
def test_notice_reflects_current_order_state(client, setores, acao, expected):
    ordem = pronta(client, setores)
    data = comando(ordem["versao"])
    if acao == "cancelamento":
        data["motivo"] = "Pedido cancelado pelo cliente"
    assert (
        client.post(
            f"/ordens/{ordem['id']}/{acao}", headers=setores["ADMIN"], json=data
        ).status_code
        == 200
    )
    notice = caixa(client, setores["SOLICITACAO"])["itens"][0]
    assert notice["situacao"] == expected
    assert notice["lida_em"] is None


def test_notification_storage_failure_rolls_back_completion(client, setores):
    ordem = nova(client, setores["SOLICITACAO"])
    for status in ("CORTANDO", "COSTURANDO"):
        ordem = avancar(client, ordem, setores["PRODUCAO"], status)

    def fail(mapper, connection, target):
        raise RuntimeError("simulated notification failure")

    event.listen(Notificacao, "before_insert", fail)
    try:
        with pytest.raises(RuntimeError, match="simulated"):
            client.patch(
                f"/ordens/{ordem['id']}/etapa",
                headers=setores["PRODUCAO"],
                json=comando(ordem["versao"], status="PRONTO"),
            )
    finally:
        event.remove(Notificacao, "before_insert", fail)
    with Session(client.app.state.engine) as session:
        saved = session.get(Ordem, ordem["id"])
        assert saved.status == "COSTURANDO" and saved.pronto_em is None and saved.versao == 3
        assert (
            len(session.exec(select(EventoOrdem).where(EventoOrdem.ordem_id == ordem["id"])).all())
            == 3
        )
        assert session.exec(select(Notificacao)).all() == []


def test_admin_creator_gets_only_one_notice_and_reads_require_auth(client, admin_headers):
    ordem = nova(client, admin_headers)
    for status in ("CORTANDO", "COSTURANDO", "PRONTO"):
        ordem = avancar(client, ordem, admin_headers, status)
    assert caixa(client, admin_headers)["nao_lidas"] == 1
    assert client.get("/notificacoes").status_code == 401
    assert client.patch("/notificacoes/1/lida").status_code == 401


def test_pagination_count_is_not_page_size(client, setores):
    for _ in range(2):
        pronta(client, setores)
    first = caixa(client, setores["ADMIN"], limit=1)
    second = caixa(client, setores["ADMIN"], limit=1, offset=1)
    assert first["nao_lidas"] == second["nao_lidas"] == 2
    assert len(first["itens"]) == 1
    assert first["itens"][0]["id"] != second["itens"][0]["id"]
