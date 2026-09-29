"""Cadastro local de funcionário; prefira o painel administrativo no uso diário."""

import argparse
from getpass import getpass

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

from backend.core.config import get_settings
from backend.database.connection import build_engine
from backend.schemas.usuario import UsuarioCreate
from backend.services.usuarios import criar_usuario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--telefone", required=True)
    parser.add_argument(
        "--setor", choices=["SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"], required=True
    )
    args = parser.parse_args()
    password = getpass("Senha (mínimo 8 caracteres): ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("Senhas diferentes")
    try:
        data = UsuarioCreate(username=args.username, telefone=args.telefone, password=password)
    except ValidationError:
        raise SystemExit(
            "Dados inválidos: confira nome, telefone com DDD e senha de 8 caracteres a 72 bytes."
        ) from None
    engine = build_engine(get_settings().DATABASE_URL)
    try:
        with Session(engine) as session:
            user = criar_usuario(session, data, setor=args.setor)
            print(f"Funcionário {user.username} criado no setor {args.setor}.")
    except HTTPException as error:
        raise SystemExit(error.detail) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
