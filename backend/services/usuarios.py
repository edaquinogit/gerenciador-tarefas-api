from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from backend.core.security import get_password_hash
from backend.models import Usuario
from backend.schemas.usuario import UsuarioCreate


def criar_usuario(session: Session, data: UsuarioCreate) -> Usuario:
    user = Usuario(
        username=data.username, email=data.email, password_hash=get_password_hash(data.password)
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Usuário ou e-mail já cadastrado") from None
    session.refresh(user)
    return user
