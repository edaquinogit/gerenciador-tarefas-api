import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select, update

from backend.core.security import get_current_user
from backend.database.connection import get_session
from backend.models import Sessao, Usuario
from backend.services import sessoes
from shared.ui_state import validar_estado

router = APIRouter(prefix="/sessoes", tags=["Sessões"])


class Codigo(BaseModel):
    code: str = Field(min_length=32, max_length=128)


class Estado(BaseModel):
    state: dict

    @field_validator("state")
    @classmethod
    def valid(cls, value):
        try:
            return validar_estado(value)
        except (ValueError, TypeError):
            raise ValueError("Estado de navegação inválido") from None


def browser(request: Request, response: Response):
    settings = request.app.state.settings
    if (
        request.headers.get("origin") not in settings.BROWSER_ORIGINS
        or request.headers.get("x-session-request") != "1"
    ):
        raise HTTPException(403, "Origem de sessão não permitida")
    response.headers["Cache-Control"] = "no-store"


@router.post("/vincular", dependencies=[Depends(browser)])
def claim(
    data: Codigo, request: Request, response: Response, session: Session = Depends(get_session)
):
    record = session.exec(
        select(Sessao).where(Sessao.codigo_hash == sessoes.digest(data.code))
    ).first()
    user = sessoes.validar(session, record)
    if record.codigo_expira_em <= sessoes.now():
        raise HTTPException(401, "Código expirado. Entre novamente.")
    secret = secrets.token_urlsafe(48)
    # Consumo atômico: duas requisições não podem reivindicar o mesmo código.
    changed = session.exec(
        update(Sessao)
        .where(
            Sessao.id == record.id,
            Sessao.codigo_hash == sessoes.digest(data.code),
            Sessao.revogada.is_(False),
        )
        .values(codigo_hash=None, cookie_hash=sessoes.digest(secret))
    )
    if changed.rowcount != 1:
        session.rollback()
        raise HTTPException(401, "Código já utilizado")
    previous_cookie = request.cookies.get(sessoes.COOKIE)
    if previous_cookie:
        session.exec(
            update(Sessao)
            .where(Sessao.cookie_hash == sessoes.digest(previous_cookie), Sessao.id != record.id)
            .values(revogada=True, cookie_hash=None, codigo_hash=None, estado="{}")
        )
    session.commit()
    session.refresh(record)
    response.set_cookie(
        sessoes.COOKIE,
        secret,
        httponly=True,
        secure=request.app.state.settings.SESSION_COOKIE_SECURE,
        samesite="strict",
        path="/sessoes",
        max_age=max(1, int((record.expira_em - sessoes.now()).total_seconds())),
    )
    return sessoes.apresentar(record, user, request.app.state.settings)


@router.post("/restaurar", dependencies=[Depends(browser)])
def restore(request: Request, session: Session = Depends(get_session)):
    cookie = request.cookies.get(sessoes.COOKIE, "")
    record = session.exec(
        select(Sessao).where(Sessao.cookie_hash == sessoes.digest(cookie))
    ).first()
    user = sessoes.validar(session, record)
    return sessoes.apresentar(record, user, request.app.state.settings)


@router.post("/limpar-cookie", dependencies=[Depends(browser)])
def clear_cookie(request: Request, response: Response, session: Session = Depends(get_session)):
    # Também revoga quando o JWT curto já expirou; apagar só o cookie não basta.
    cookie = request.cookies.get(sessoes.COOKIE)
    if cookie:
        session.exec(
            update(Sessao)
            .where(Sessao.cookie_hash == sessoes.digest(cookie))
            .values(revogada=True, cookie_hash=None, codigo_hash=None, estado="{}")
        )
        session.commit()
    response.delete_cookie(sessoes.COOKIE, path="/sessoes", httponly=True, samesite="strict")
    return {"message": "Cookie removido"}


@router.post("/sair")
def logout(
    request: Request,
    user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    record = request.state.login_session
    session.exec(
        update(Sessao)
        .where(Sessao.id == record.id)
        .values(revogada=True, cookie_hash=None, codigo_hash=None, estado="{}")
    )
    session.commit()
    return {"message": "Sessão encerrada"}


@router.get("/estado")
def get_state(request: Request, user: Usuario = Depends(get_current_user)):
    return {"state": json.loads(request.state.login_session.estado)}


@router.put("/estado")
def save_state(
    data: Estado,
    request: Request,
    user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session.exec(
        update(Sessao)
        .where(Sessao.id == request.state.login_session.id, Sessao.revogada.is_(False))
        .values(estado=json.dumps(data.state, ensure_ascii=False))
    )
    session.commit()
    return {"message": "Navegação e rascunho salvos"}
