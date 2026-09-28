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
