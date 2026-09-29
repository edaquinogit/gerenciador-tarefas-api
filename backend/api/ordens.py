from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from backend.core.security import get_current_user
from backend.database.connection import get_session
from backend.models import Usuario
from backend.models.ordem import EventoOrdem
from backend.schemas.ordem import (
    Cancelamento,
    ComandoOrdem,
    EtapaUpdate,
    EventoRead,
    OrdemCreate,
    OrdemRead,
    StatusOrdem,
)
from backend.services import ordens

router = APIRouter(prefix="/ordens", tags=["Ordens compartilhadas"])


@router.post("", response_model=OrdemRead, status_code=201)
def criar(
    data: OrdemCreate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return ordens.apresentar(session, ordens.criar(session, data, user))


@router.get("", response_model=list[OrdemRead])
def listar(
    status: StatusOrdem | None = None,
    situacao: Literal["ativas", "coletadas", "canceladas", "todas"] = "ativas",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return [
        ordens.apresentar(session, item)
        for item in ordens.listar(session, user, status, situacao, offset, limit)
    ]


@router.get("/{ident}", response_model=OrdemRead)
def detalhe(
    ident: int, session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)
):
    ordens.permitir(user)
    return ordens.apresentar(session, ordens.buscar(session, ident))


@router.get("/{ident}/historico", response_model=list[EventoRead])
def historico(
    ident: int, session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)
):
    ordens.permitir(user)
    ordens.buscar(session, ident)
    return session.exec(
        select(EventoOrdem).where(EventoOrdem.ordem_id == ident).order_by(EventoOrdem.versao)
    ).all()


@router.patch("/{ident}/etapa", response_model=OrdemRead)
def etapa(
    ident: int,
    data: EtapaUpdate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return ordens.apresentar(
        session, ordens.executar(session, ident, data, user, "ETAPA", destino=data.status)
    )


@router.post("/{ident}/coleta", response_model=OrdemRead)
def coleta(
    ident: int,
    data: ComandoOrdem,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return ordens.apresentar(session, ordens.executar(session, ident, data, user, "COLETA"))


@router.post("/{ident}/cancelamento", response_model=OrdemRead)
def cancelar(
    ident: int,
    data: Cancelamento,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return ordens.apresentar(
        session, ordens.executar(session, ident, data, user, "CANCELAMENTO", motivo=data.motivo)
    )
