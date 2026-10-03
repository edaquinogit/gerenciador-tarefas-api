from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from backend.core.security import get_current_user
from backend.database.connection import get_session
from backend.models import Usuario
from backend.schemas.notificacao import CaixaAvisos
from backend.services import notificacoes

router = APIRouter(prefix="/notificacoes", tags=["Avisos de produtos"])


def destinatario(user: Usuario = Depends(get_current_user)):
    return user


@router.get("", response_model=CaixaAvisos)
def listar(
    somente_nao_lidas: bool = True,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    user: Usuario = Depends(destinatario),
):
    return notificacoes.listar(session, user, somente_nao_lidas, offset, limit)


@router.patch("/{ident}/lida")
def lida(
    ident: int, session: Session = Depends(get_session), user: Usuario = Depends(destinatario)
):
    return notificacoes.marcar_lida(session, ident, user)
