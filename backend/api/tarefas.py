from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.core.security import get_current_user
from backend.database.connection import get_session
from backend.models import Usuario
from backend.schemas.tarefa import TarefaCreate, TarefaRead
from backend.services import tarefas

router = APIRouter(prefix="/tarefas", tags=["Tarefas"])


@router.get("", response_model=list[TarefaRead])
def listar(session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)):
    return tarefas.listar(session, user.id)


@router.post("", response_model=TarefaRead, status_code=201)
def criar(
    data: TarefaCreate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return tarefas.criar(session, data, user.id)


@router.patch("/{tarefa_id}/concluir", response_model=TarefaRead)
def concluir(
    tarefa_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return tarefas.concluir(session, tarefa_id, user.id)


@router.delete("/{tarefa_id}")
def deletar(
    tarefa_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    tarefas.deletar(session, tarefa_id, user.id)
    return {"detail": "Tarefa removida com sucesso"}
