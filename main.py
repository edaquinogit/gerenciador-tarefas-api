from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlmodel import select, SQLModel
from datetime import timedelta
from typing import List
from contextlib import asynccontextmanager

# Importações internas
from database import get_session, engine
from models import Usuario, Tarefa, UsuarioCreate, TarefaCreate, Token
from security import (
    get_current_user, authenticate_user, create_access_token, 
    gerar_hash_senha, ACCESS_TOKEN_EXPIRE_MINUTES
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas automaticamente no Render ao iniciar
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="Gerenciador de Tarefas API",
    description="API robusta com SQLModel, FastAPI e Autenticação JWT",
    version="2.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

# Permite que o frontend (Streamlit) acesse a API sem bloqueios de segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/token", response_model=Token, tags=["Segurança"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROTAS DE USUÁRIOS (CADASTRO LIBERADO) ---

@app.post("/usuarios", status_code=status.HTTP_201_CREATED, tags=["Administração"])
def criar_usuario(
    usuario: UsuarioCreate, 
    session: Session = Depends(get_session)
):
    # Verifica se o usuário já existe
    statement = select(Usuario).where(Usuario.username == usuario.username)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Utilizador já cadastrado")
    
    novo_usuario = Usuario(
        username=usuario.username,
        email=usuario.email,
        password_hash=gerar_hash_senha(usuario.password),
        is_active=True,
        is_admin=False # O primeiro usuário criado será comum
    )
    session.add(novo_usuario)
    session.commit()
    return {"message": f"Utilizador {usuario.username} criado com sucesso!"}

# --- ROTAS DE TAREFAS ---

@app.get("/tarefas", response_model=List[Tarefa], tags=["Tarefas"])
def listar_tarefas(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.is_admin:
        statement = select(Tarefa)
    else:
        statement = select(Tarefa).where(Tarefa.usuario_id == current_user.id)
        
    return session.exec(statement).all()

@app.post("/tarefas", response_model=Tarefa, tags=["Tarefas"])
def criar_tarefa(
    tarefa_input: TarefaCreate, 
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    nova_tarefa = Tarefa(
        **tarefa_input.model_dump(),
        concluido=False,
        usuario_id=current_user.id
    )
    session.add(nova_tarefa)
    session.commit()
    session.refresh(nova_tarefa)
    return nova_tarefa

@app.patch("/tarefas/{tarefa_id}/concluir", tags=["Tarefas"])
def concluir_tarefa(
    tarefa_id: int, 
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    statement = select(Tarefa).where(Tarefa.id == tarefa_id, Tarefa.usuario_id == current_user.id)