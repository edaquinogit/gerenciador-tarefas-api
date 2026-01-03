from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from models import Tarefa, crie_o_banco
from database import get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    crie_o_banco()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return {"mensagem": "API de Tarefas Online"}


@app.post("/tarefas")
def criar_tarefa(tarefa: Tarefa, session: Session = Depends(get_session)):
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa


@app.get("/tarefas")
def listar_tarefas(
    session: Session = Depends(get_session),
    concluida: bool | None = None,
    termo: str | None = None
):
    statement = select(Tarefa)

    if concluida is not None:
        statement = statement.where(Tarefa.concluida == concluida)

    if termo:
        statement = statement.where(Tarefa.titulo.contains(termo))

    tarefas = session.exec(statement).all()
    return tarefas


@app.patch("/tarefas/{tarefa_id}")
def atualizar_tarefa(tarefa_id: int, session: Session = Depends(get_session)):
    tarefa = session.get(Tarefa, tarefa_id)

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    tarefa.concluida = True
    session.commit()
    session.refresh(tarefa)
    return tarefa


@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(tarefa_id: int, session: Session = Depends(get_session)):
    tarefa = session.get(Tarefa, tarefa_id)

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    session.delete(tarefa)
    session.commit()

    return {"mensagem": "Deletado com sucesso!"}
