"""Cria o primeiro administrador localmente, sem senha fixa ou promoção automática."""

import argparse
from getpass import getpass

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

from backend.core.config import get_settings
from backend.database.connection import build_engine
from backend.schemas.usuario import UsuarioCreate
from backend.services.usuarios import criar_primeiro_admin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Senha do administrador (mínimo 8 caracteres): ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("Senhas diferentes")
    try:
        data = UsuarioCreate(username=args.username, email=args.email, password=password)
    except ValidationError:
        raise SystemExit(
            "Dados inválidos: confira nome, e-mail e senha de 8 caracteres a 72 bytes."
        ) from None
    engine = build_engine(get_settings().DATABASE_URL)
    try:
        with Session(engine) as session:
            user = criar_primeiro_admin(session, data)
            print(
                f"Administrador {user.username} criado. Entre no painel para cadastrar funcionários."
            )
    except HTTPException as error:
        raise SystemExit(error.detail) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
