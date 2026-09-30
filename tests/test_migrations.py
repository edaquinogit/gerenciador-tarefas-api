import os
import subprocess
import sys

from sqlalchemy import inspect, text

from backend.database.connection import build_engine
from backend.database.legacy import metadata


def run(*args, url):
    env = {
        **os.environ,
        "DATABASE_URL": url,
        "SECRET_KEY": "test-only-migration-key-at-least-32-chars",
    }
    return subprocess.run([sys.executable, *args], env=env, text=True, capture_output=True)


def test_fresh_database_and_no_schema_drift(tmp_path):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    result = run("-m", "alembic", "upgrade", "head", url=url)
    assert result.returncode == 0, result.stderr
    engine = build_engine(url)
    assert set(inspect(engine).get_table_names()) == {
        "usuario",
        "tarefa",
        "ordem",
        "eventoordem",
        "notificacao",
        "alembic_version",
    }
    result = run("-m", "alembic", "check", url=url)
    assert result.returncode == 0, result.stdout + result.stderr
    engine.dispose()


def test_adopt_legacy_preserves_data(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine = build_engine(url)
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO usuario VALUES (1, 'legado', 'legado@example.com', 'hash', 1)")
        )
        conn.execute(text("INSERT INTO tarefa VALUES (1, 'Tarefa existente', 'Média', 1, 1)"))
    result = run("-m", "backend.scripts.adotar_banco", url=url)
    assert result.returncode == 0, result.stdout + result.stderr
    with engine.connect() as conn:
        assert conn.execute(text("SELECT titulo, concluido FROM tarefa")).one() == (
            "Tarefa existente",
            1,
        )
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0001"
    result = run("-m", "alembic", "upgrade", "head", url=url)
    assert result.returncode == 0, result.stderr
    with engine.connect() as conn:
        assert conn.execute(text("SELECT perfil, setor, token_version FROM usuario")).one() == (
            "FUNCIONARIO",
            None,
            0,
        )
        assert conn.execute(text("SELECT titulo, concluido FROM tarefa")).one() == (
            "Tarefa existente",
            1,
        )
    engine.dispose()


def test_adopt_refuses_unknown_schema(tmp_path):
    url = f"sqlite:///{tmp_path / 'other.db'}"
    engine = build_engine(url)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE importante (id INTEGER)"))
    result = run("-m", "backend.scripts.adotar_banco", url=url)
    assert result.returncode != 0
    assert set(inspect(engine).get_table_names()) == {"importante"}
    engine.dispose()


def seed_v4(url):
    from datetime import datetime

    from sqlalchemy import MetaData

    from backend.core.security import get_password_hash
    from backend.models import Tarefa, Usuario
    from backend.models.notificacao import Notificacao
    from backend.models.ordem import EventoOrdem, Ordem

    result = run("-m", "alembic", "upgrade", "0004", url=url)
    assert result.returncode == 0, result.stderr
    engine = build_engine(url)
    schema = MetaData()
    schema.reflect(engine)
    records = [
        Usuario(
            id=1,
            username="legado",
            email="old@example.com",
            password_hash=get_password_hash("senha-legado-123"),
            perfil="ADMIN",
        ),
        Tarefa(id=1, titulo="Preservar tarefa", usuario_id=1),
        Ordem(
            id=1,
            request_id="ordem-antiga",
            produto="Lote antigo",
            especificacao="Teste",
            quantidade=10,
            unidade="pecas",
            prioridade="NORMAL",
            prazo=datetime(2026, 10, 1),
            observacao="",
            status="PRONTO",
            solicitante_id=1,
            responsavel_id=1,
            pronto_em=datetime(2026, 9, 28),
            versao=4,
        ),
        EventoOrdem(
            id=1,
            request_id="evento-antigo",
            ordem_id=1,
            usuario_id=1,
            usuario_nome="legado",
            acao="ETAPA",
            status_anterior="COSTURANDO",
            status_novo="PRONTO",
            versao=4,
        ),
        Notificacao(
            id=1,
            evento_id=1,
            ordem_id=1,
            usuario_id=1,
            mensagem="Produto pronto",
            lida_em=datetime(2026, 9, 28),
        ),
    ]
    with engine.begin() as conn:
        for record in records:
            table = schema.tables[record.__tablename__]
            conn.execute(
                table.insert().values(
                    **{k: v for k, v in record.model_dump().items() if k in table.c}
                )
            )
    engine.dispose()


def test_v5_preserves_all_data_and_legacy_login(tmp_path):
    from fastapi.testclient import TestClient

    from backend.core.config import Settings
    from backend.main import create_app

    url = f"sqlite:///{tmp_path / 'v4.db'}"
    seed_v4(url)
    engine = build_engine(url)
    tables = ("usuario", "tarefa", "ordem", "eventoordem", "notificacao")
    with engine.connect() as conn:
        before = {
            table: dict(conn.execute(text(f"SELECT * FROM {table}")).mappings().one())
            for table in tables
        }
    result = run("-m", "alembic", "upgrade", "head", url=url)
    assert result.returncode == 0, result.stderr
    with engine.connect() as conn:
        for table in tables:
            after = dict(conn.execute(text(f"SELECT * FROM {table}")).mappings().one())
            if table == "usuario":
                assert after.pop("telefone") is None
            elif table == "ordem":
                assert after.pop("categoria") == "OUTROS"
            assert after == before[table]
        assert not conn.exec_driver_sql("PRAGMA foreign_key_check").all()
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    settings = Settings(_env_file=None, SECRET_KEY="test-migration-secret-with-32-characters")
    with TestClient(create_app(settings, engine)) as client:
        login = client.post("/token", data={"username": "legado", "password": "senha-legado-123"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/usuarios/me", headers=headers).json()["telefone"] is None
        assert client.get(
            "/notificacoes", headers=headers, params={"somente_nao_lidas": False}
        ).json()["itens"][0]["lida_em"]
        assert (
            client.patch(
                "/usuarios/me/telefone", headers=headers, json={"telefone": "79999990001"}
            ).status_code
            == 200
        )
        response = client.post(
            "/admin/funcionarios",
            headers=headers,
            json={
                "username": "novo",
                "telefone": "79999990002",
                "password": "senha-nova-123",
                "setor": "PRODUCAO",
            },
        )
        assert response.status_code == 201
    engine.dispose()
    assert run("-m", "alembic", "check", url=url).returncode == 0


def test_invalid_references_rollback_v5_including_schema(tmp_path):
    import sqlite3

    path = tmp_path / "invalid.db"
    url = f"sqlite:///{path}"
    seed_v4(url)
    # Simula corrupção prévia sem desativar verificações na aplicação.
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE tarefa SET usuario_id=999 WHERE id=1")
    result = run("-m", "alembic", "upgrade", "head", url=url)
    assert result.returncode != 0
    assert "referências inválidas" in result.stderr
    engine = build_engine(url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0004"
        assert conn.execute(text("SELECT email FROM usuario")).scalar() == "old@example.com"
    assert "telefone" not in {column["name"] for column in inspect(engine).get_columns("usuario")}
    assert "_alembic_tmp_usuario" not in inspect(engine).get_table_names()
    engine.dispose()


def test_v6_preserves_orders_history_and_notifications(tmp_path):
    url = f"sqlite:///{tmp_path / 'v5-to-v6.db'}"
    seed_v4(url)
    result = run("-m", "alembic", "upgrade", "0005", url=url)
    assert result.returncode == 0, result.stderr
    engine = build_engine(url)
    tables = ("usuario", "tarefa", "ordem", "eventoordem", "notificacao")
    with engine.connect() as conn:
        before = {
            t: dict(conn.execute(text(f"SELECT * FROM {t}")).mappings().one()) for t in tables
        }
    result = run("-m", "alembic", "upgrade", "head", url=url)
    assert result.returncode == 0, result.stderr
    with engine.connect() as conn:
        for table in tables:
            after = dict(conn.execute(text(f"SELECT * FROM {table}")).mappings().one())
            if table == "ordem":
                assert after.pop("categoria") == "OUTROS"
            assert after == before[table]
        assert not conn.exec_driver_sql("PRAGMA foreign_key_check").all()
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0006"
    engine.dispose()
    assert run("-m", "alembic", "check", url=url).returncode == 0
    assert run("-m", "alembic", "downgrade", "0005", url=url).returncode != 0
