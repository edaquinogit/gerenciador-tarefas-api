"""Cadastro local de usuário comum até a implementação dos perfis."""

import argparse
from getpass import getpass

from sqlmodel import Session

from backend.core.config import get_settings
from backend.database.connection import build_engine
from backend.schemas.usuario import UsuarioCreate
from backend.services.usuarios import criar_usuario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Senha (mínimo 8 caracteres): ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("Senhas diferentes")
    data = UsuarioCreate(username=args.username, email=args.email, password=password)
    engine = build_engine(get_settings().DATABASE_URL)
    try:
        with Session(engine) as session:
            user = criar_usuario(session, data)
            print(
                f"Usuário {user.username} criado. Perfis administrativos serão implementados na próxima fase."
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
