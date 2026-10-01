import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.core.config import Settings
from backend.database.connection import build_engine
from backend.main import create_app
from backend.models import Usuario
from backend.scripts.piloto import environment, prepare
from tests.test_ordens import avancar, comando, nova


def test_isolated_pilot_complete_flow_and_persistence(tmp_path, monkeypatch):
    original = tmp_path / "original.db"
    original.write_bytes(b"Banco da empresa: nao modificar")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{original}")
    monkeypatch.setenv("ALLOW_REGISTRATION", "true")
    directory = tmp_path / "ensaio"
    prepare(directory)
    assert original.read_bytes() == b"Banco da empresa: nao modificar"
    config = json.loads((directory / "config.json").read_text())
    env = environment(directory, config["secret"])
    assert env["ALLOW_REGISTRATION"] == "false"
    accounts = json.loads((directory / "acessos.json").read_text())
    assert len({item["senha"] for item in accounts}) == 4
    engine = build_engine(env["DATABASE_URL"])
    settings = Settings(_env_file=None, SECRET_KEY=config["secret"], ALLOW_REGISTRATION=False)
    with TestClient(create_app(settings, engine)) as client:
        headers = {}
        for account in accounts:
            response = client.post(
                "/token", data={"username": account["usuario"], "password": account["senha"]}
            )
            assert response.status_code == 200
            headers[account["setor"] or "ADMIN"] = {
                "Authorization": f"Bearer {response.json()['access_token']}"
            }
        assert client.get("/admin/funcionarios", headers=headers["PRODUCAO"]).status_code == 403
        order = nova(client, headers["SOLICITACAO"])
        assert (
            client.patch(
                f"/ordens/{order['id']}/etapa",
                headers=headers["SOLICITACAO"],
                json=comando(order["versao"], status="CORTANDO"),
            ).status_code
            == 403
        )
        for status in ("CORTANDO", "COSTURANDO", "PRONTO"):
            order = avancar(client, order, headers["PRODUCAO"], status)
        for role in ("ADMIN", "SOLICITACAO", "COLETA_EMBALAGEM"):
            assert client.get("/notificacoes", headers=headers[role]).json()["nao_lidas"] == 1
        notice = client.get("/notificacoes", headers=headers["COLETA_EMBALAGEM"]).json()["itens"][0]
        assert (
            client.patch(
                f"/notificacoes/{notice['id']}/lida", headers=headers["COLETA_EMBALAGEM"]
            ).status_code
            == 200
        )
        assert (
            client.get(f"/ordens/{order['id']}", headers=headers["ADMIN"]).json()["coletado_em"]
            is None
        )
        assert (
            client.post(
                f"/ordens/{order['id']}/coleta",
                headers=headers["COLETA_EMBALAGEM"],
                json=comando(order["versao"]),
            ).status_code
            == 200
        )
    engine.dispose()
    # Nova conexão/aplicação: aviso e coleta sobrevivem ao encerramento.
    engine = build_engine(env["DATABASE_URL"])
    with TestClient(create_app(settings, engine)) as client:
        assert client.get(f"/ordens/{order['id']}", headers=headers["ADMIN"]).json()["coletado_em"]
        notices = client.get("/notificacoes", headers=headers["SOLICITACAO"]).json()
        assert notices["itens"][0]["situacao"] == "COLETADA"
    with Session(engine) as session:
        assert len(session.exec(select(Usuario)).all()) == 4
    engine.dispose()
    before = (directory / "config.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare(directory)
    assert (directory / "config.json").read_bytes() == before


def test_failed_setup_has_no_ready_marker(tmp_path, monkeypatch):
    import subprocess

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "alembic")

    monkeypatch.setattr(subprocess, "run", fail)
    directory = tmp_path / "incompleto"
    with pytest.raises(subprocess.CalledProcessError):
        prepare(directory)
    assert not (directory / "config.json").exists()


def test_pilot_browser_addresses_are_same_host_and_restricted(tmp_path):
    local = environment(tmp_path, "test-only-secret")
    assert local["PUBLIC_API_URL"] == ""
    assert local["PUBLIC_API_PORT"] == "8001"
    assert json.loads(local["BROWSER_ORIGINS"]) == [
        "http://127.0.0.1:8502",
        "http://localhost:8502",
    ]
    network = environment(tmp_path, "test-only-secret", "192.168.1.20")
    assert "http://192.168.1.20:8502" in json.loads(network["BROWSER_ORIGINS"])
    with pytest.raises(ValueError):
        environment(tmp_path, "test-only-secret", "0.0.0.0")
