"""Consulta global de tarefas reservada ao administrador."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from backend.core.security import require_admin
from backend.database.connection import get_session
from backend.models import Tarefa, Usuario
from backend.schemas.tarefa import TarefaRead

router = APIRouter(prefix="/admin", tags=["Painel administrativo"])


class TarefaAdministrativa(TarefaRead):
    usuario_nome: str
    setor: str | None


class PaginaTarefas(BaseModel):
    total: int
    itens: list[TarefaAdministrativa]


@router.get("/tarefas", response_model=PaginaTarefas)
def listar_todas(
    concluido: bool | None = None,
    usuario_id: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    admin: Usuario = Depends(require_admin),
):
    filters = []
    if concluido is not None:
        filters.append(Tarefa.concluido == concluido)
    if usuario_id is not None:
        filters.append(Tarefa.usuario_id == usuario_id)
    total = session.exec(select(func.count()).select_from(Tarefa).where(*filters)).one()
    rows = session.exec(
        select(Tarefa, Usuario.username, Usuario.setor)
        .join(Usuario, Tarefa.usuario_id == Usuario.id)
        .where(*filters)
        .order_by(Tarefa.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return PaginaTarefas(
        total=total,
        itens=[
            TarefaAdministrativa(**task.model_dump(), usuario_nome=name, setor=sector)
            for task, name, sector in rows
        ],
    )
