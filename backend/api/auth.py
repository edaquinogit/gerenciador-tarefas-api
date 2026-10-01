from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from backend.core.security import authenticate_user, create_access_token, get_current_user
from backend.database.connection import get_session
from backend.models import Usuario
from backend.schemas.usuario import Token, UsuarioCreate, UsuarioRead
from backend.services.sessoes import criar
from backend.services.usuarios import criar_usuario

router = APIRouter(tags=["Acesso"])


@router.post("/token", response_model=Token)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form.username, form.password)
    if not user:
        raise HTTPException(
            401, "Usuário ou senha incorretos", headers={"WWW-Authenticate": "Bearer"}
        )
    record, code = criar(session, user, request.app.state.settings)
    return Token(
        browser_code=code,
        access_token=create_access_token(
            user.username, request.app.state.settings, user.token_version, record.id
        ),
    )


@router.get("/usuarios/me", response_model=UsuarioRead)
def me(user: Usuario = Depends(get_current_user)):
    return user


@router.post("/usuarios", status_code=201)
def register(data: UsuarioCreate, request: Request, session: Session = Depends(get_session)):
    if not request.app.state.settings.ALLOW_REGISTRATION:
        raise HTTPException(403, "Cadastro público desativado. Solicite acesso ao responsável.")
    criar_usuario(session, data)
    return {"message": "Usuário criado com sucesso"}
