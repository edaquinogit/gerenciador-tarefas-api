from fastapi import HTTPException
from sqlmodel import Session, select

from backend.models import Tarefa
from backend.schemas.tarefa import TarefaCreate


def listar(session: Session, usuario_id: int) -> list[Tarefa]:
    return list(
        session.exec(
            select(Tarefa).where(Tarefa.usuario_id == usuario_id).order_by(Tarefa.id.desc())
        ).all()
    )


def criar(session: Session, data: TarefaCreate, usuario_id: int) -> Tarefa:
    tarefa = Tarefa(**data.model_dump(), usuario_id=usuario_id)
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa


def buscar(session: Session, tarefa_id: int, usuario_id: int) -> Tarefa:
    tarefa = session.exec(
        select(Tarefa).where(Tarefa.id == tarefa_id, Tarefa.usuario_id == usuario_id)
    ).first()
    if tarefa is None:
        raise HTTPException(404, "Tarefa não encontrada")
    return tarefa


def concluir(session: Session, tarefa_id: int, usuario_id: int) -> Tarefa:
    tarefa = buscar(session, tarefa_id, usuario_id)
    tarefa.concluido = True
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa


def deletar(session: Session, tarefa_id: int, usuario_id: int) -> None:
    session.delete(buscar(session, tarefa_id, usuario_id))
    session.commit()
