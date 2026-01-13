import sys
import os

# 1. Configuração de Caminho (Sempre no topo!)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# 2. Imports de Bibliotecas Externas
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select, Session
from datetime import timedelta
from typing import List
from contextlib import asynccontextmanager

# 3. Imports Internos do Projeto (Agora o Python acha eles!)
from database.connection import get_session, engine
from schemas.models import Usuario, Tarefa, UsuarioCreate, TarefaCreate, Token
from core.security import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from core.config import settings

# =========================
# CICLO DE VIDA (Lifespan)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Isso cria as tabelas no arquivo .db automaticamente
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="Gerenciador de Tarefas API",
    description="API robusta para gerenciamento de tarefas pessoais",
    version="2.0.0",
    lifespan=lifespan,
)

# =========================
# MIDDLEWARE (CORS)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROTAS (Endpoints)
# =========================

@app.post("/token", response_model=Token, tags=["Auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.username},
        expires_delta=expires,
    )
    return {"access_token": token, "token_type": "bearer"}

@app.post("/usuarios", status_code=status.HTTP_201_CREATED, tags=["Usuários"])
def criar_usuario(
    usuario: UsuarioCreate,
    session: Session = Depends(get_session),
):
    existe = session.exec(
        select(Usuario).where(Usuario.username == usuario.username)
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    novo = Usuario(
        username=usuario.username,
        email=usuario.email,
        password_hash=get_password_hash(usuario.password),
    )
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return {"message": "Usuário criado com sucesso"}

@app.get("/tarefas", response_model=List[Tarefa], tags=["Tarefas"])
def listar_tarefas(
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return session.exec(
        select(Tarefa).where(Tarefa.usuario_id == user.id)
    ).all()

@app.post("/tarefas", response_model=Tarefa, tags=["Tarefas"])
def criar_tarefa(
    tarefa: TarefaCreate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    nova = Tarefa(
        **tarefa.model_dump(),
        usuario_id=user.id,
    )
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return nova

@app.patch("/tarefas/{tarefa_id}/concluir", response_model=Tarefa, tags=["Tarefas"])
def concluir_tarefa(
    tarefa_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    tarefa = session.exec(
        select(Tarefa).where(
            Tarefa.id == tarefa_id,
            Tarefa.usuario_id == user.id,
        )
    ).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    tarefa.concluido = not tarefa.concluido
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.delete("/tarefas/{tarefa_id}", tags=["Tarefas"])
def deletar_tarefa(
    tarefa_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    tarefa = session.exec(
        select(Tarefa).where(
            Tarefa.id == tarefa_id,
            Tarefa.usuario_id == user.id,
        )
    ).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    session.delete(tarefa)
    session.commit()
    return {"detail": "Tarefa removida com sucesso"}