import os
import subprocess
import sys

from sqlmodel import Session, select

from backend.core.security import verify_password
from backend.database.connection import build_engine
from backend.models import Usuario


def test_bootstrap_command_and_local_employee_command(tmp_path):
    url = f"sqlite:///{tmp_path / 'bootstrap.db'}"
    env = {
        **os.environ,
        "DATABASE_URL": url,
        "SECRET_KEY": "test-only-bootstrap-secret-with-32-characters",
    }

    def run(*args, password=None):
        return subprocess.run(
            [sys.executable, *args],
            env=env,
            input=f"{password}\n{password}\n" if password else None,
            capture_output=True,
            text=True,
        )

    result = run("-m", "alembic", "upgrade", "head")
    assert result.returncode == 0, result.stderr
    args = (
        "-m",
        "backend.scripts.criar_admin",
        "--username",
        "patrao",
        "--email",
        "patrao@example.com",
    )
    result = run(*args, password="senha-admin-123")
    assert result.returncode == 0, result.stderr
    assert "senha-admin-123" not in result.stdout + result.stderr
    duplicate = run(*args, password="senha-nova-123")
    assert duplicate.returncode != 0
    assert "Administrador já existe" in duplicate.stderr
    result = run(
        "-m",
        "backend.scripts.criar_usuario",
        "--username",
        "operador",
        "--email",
        "operador@example.com",
        "--setor",
        "PRODUCAO",
        password="senha-func-123",
    )
    assert result.returncode == 0, result.stderr
    engine = build_engine(url)
    with Session(engine) as session:
        admin = session.exec(select(Usuario).where(Usuario.username == "patrao")).one()
        assert admin.perfil == "ADMIN" and admin.setor is None
        assert verify_password("senha-admin-123", admin.password_hash)
        funcionario = session.exec(select(Usuario).where(Usuario.username == "operador")).one()
        assert funcionario.perfil == "FUNCIONARIO" and funcionario.setor == "PRODUCAO"
    engine.dispose()
