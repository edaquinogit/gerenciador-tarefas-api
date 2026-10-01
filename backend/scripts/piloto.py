"""Ambiente descartável para ensaio entre setores, sem usar o banco da empresa."""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / ".pilot"
ACCOUNTS = (
    ("piloto_admin", "ADMIN", None),
    ("piloto_solicitacao", "FUNCIONARIO", "SOLICITACAO"),
    ("piloto_producao", "FUNCIONARIO", "PRODUCAO"),
    ("piloto_coleta", "FUNCIONARIO", "COLETA_EMBALAGEM"),
)


def environment(directory: Path, secret: str) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(ROOT),
        "SECRET_KEY": secret,
        "DATABASE_URL": f"sqlite:///{(directory / 'piloto.db').resolve().as_posix()}",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "ALLOW_REGISTRATION": "false",
        "CORS_ORIGINS": "[]",
        "API_URL": "http://127.0.0.1:8001",
        "PUBLIC_API_URL": "http://127.0.0.1:8001",
        "BROWSER_ORIGINS": '["http://127.0.0.1:8502"]',
        "SESSION_COOKIE_SECURE": "false",
        "PILOT_MODE": "true",
    }


def private_write(path: Path, content: str):
    # No Windows, use também as permissões da pasta do usuário.
    with path.open("x", encoding="utf-8") as file:
        path.chmod(0o600)
        file.write(content)


def prepare(directory: Path = PILOT):
    from sqlmodel import Session

    from backend.database.connection import build_engine
    from backend.schemas.usuario import UsuarioCreate
    from backend.services.usuarios import criar_usuario

    directory.mkdir(mode=0o700)  # Recusa sobrescrever qualquer ensaio anterior.
    secret = secrets.token_urlsafe(48)
    env = environment(directory, secret)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    engine = build_engine(env["DATABASE_URL"])
    credentials = []
    try:
        with Session(engine) as session:
            for index, (username, role, sector) in enumerate(ACCOUNTS, start=1):
                password = secrets.token_urlsafe(18)
                criar_usuario(
                    session,
                    UsuarioCreate(
                        username=username, telefone=f"7999999000{index}", password=password
                    ),
                    perfil=role,
                    setor=sector,
                )
                credentials.append({"usuario": username, "senha": password, "setor": sector})
        private_write(directory / "acessos.json", json.dumps(credentials, indent=2))
        # Marcador só existe quando migrações e todas as contas foram criadas.
        private_write(directory / "config.json", json.dumps({"secret": secret, "version": 1}))
    finally:
        engine.dispose()
    print(f"Ensaio preparado. Consulte as senhas somente em {directory / 'acessos.json'}")


def stop(processes):
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def start(network: bool = False, directory: Path = PILOT):
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    if config.get("version") != 1 or len(config.get("secret", "")) < 32:
        raise ValueError("Configuração de ensaio inválida")
    if not (directory / "piloto.db").is_file():
        raise ValueError("Banco de ensaio ausente; restaure a pasta completa")
    env = environment(directory, config["secret"])
    # Recusa portas ocupadas em vez de conectar a outro sistema por engano.
    for port in (8001, 8502):
        with socket.socket() as sock:
            sock.bind(("0.0.0.0", port))
    subprocess.run([sys.executable, "-m", "alembic", "check"], cwd=ROOT, env=env, check=True)
    processes = []
    try:
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8001",
                ],
                cwd=ROOT,
                env=env,
            )
        )
        for _ in range(100):
            if processes[0].poll() is not None:
                raise RuntimeError("API encerrou antes de ficar disponível")
            try:
                with urlopen(env["API_URL"] + "/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                time.sleep(0.2)
        else:
            raise RuntimeError("API não ficou disponível")
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "frontend/app.py",
                    "--server.address",
                    "0.0.0.0" if network else "127.0.0.1",
                    "--server.port",
                    "8502",
                    "--server.headless",
                    "true",
                    "--browser.gatherUsageStats",
                    "false",
                ],
                cwd=ROOT,
                env=env,
            )
        )
        print("TESTE: http://localhost:8502 — Ctrl+C encerra API e interface.", flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        raise RuntimeError("Um dos serviços encerrou; o ensaio foi interrompido")
    finally:
        stop(processes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("preparar", "iniciar"))
    parser.add_argument("--rede", action="store_true", help="Interface na rede local confiável")
    args = parser.parse_args()
    try:
        if args.acao == "preparar":
            if args.rede:
                parser.error("--rede é usado somente com iniciar")
            prepare()
        else:
            start(args.rede)
    except KeyboardInterrupt:
        print("Ensaio encerrado. Os dados ficam preservados em .pilot.")
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError):
        parser.exit(
            1,
            "Não foi possível preparar/iniciar. Confira .pilot, dependências e portas "
            "8001/8502. Não apague dados para corrigir: consulte docs/piloto.md.\n",
        )


if __name__ == "__main__":
    main()
