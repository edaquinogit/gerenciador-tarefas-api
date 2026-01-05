from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
from sqlmodel import Session, select
from models import Tarefa, Prioridade, Usuario
from database import get_session, create_db_and_tabelas
from security import verificar_senha, criar_token_acesso, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from sqlalchemy import func

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tabelas()
    yield

app = FastAPI(lifespan=lifespan)

# Dependência para autenticação 🔐
def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Erro ao validar token")
    
    usuario = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return usuario

# Rota de Login (única!) 🔑
@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    statement = select(Usuario).where(Usuario.username == form_data.username)
    usuario = session.exec(statement).first()

    if not usuario or not verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=400, 
            detail="Usuário ou senha incorretos"
        )

    token = criar_token_acesso(dados={"sub": usuario.username})
    return {"access_token": token, "token_type": "bearer"}

# CRUD de Tarefas 📝
@app.post("/tarefas")
def criar_tarefa(
    tarefa: Tarefa, 
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    tarefa.usuario_id = usuario_logado.id
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.get("/tarefas", response_model=list[Tarefa])
def listar_tarefas(
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual),
    concluido: bool = None, 
    termo: str = None,
    prioridade: Prioridade = None
):
    statement = select(Tarefa).where(Tarefa.usuario_id == usuario_logado.id)
    if concluido is not None:
        statement = statement.where(Tarefa.concluido == concluido) 
    if termo:
        statement = statement.where(Tarefa.titulo.contains(termo))
    if prioridade:
        statement = statement.where(Tarefa.prioridade == prioridade)
    
    return session.exec(statement).all()

@app.patch("/tarefas/{tarefa_id}")
def editar_tarefa(
    tarefa_id: int,
    tarefa_atualizada: dict,
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    tarefa_db = session.get(Tarefa, tarefa_id)
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if tarefa_db.usuario_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    for chave, valor in tarefa_atualizada.items():
        setattr(tarefa_db, chave, valor)

    session.add(tarefa_db)
    session.commit()
    session.refresh(tarefa_db)
    return tarefa_db

# Rota de Estatísticas (confirmada como GET) 📊
@app.get("/tarefas/estatisticas")
def obter_estatisticas(
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    query_total = select(func.count(Tarefa.id)).where(Tarefa.usuario_id == usuario_logado.id)
    total = session.exec(query_total).one()
    
    query_concluidas = select(func.count(Tarefa.id)).where(
        Tarefa.usuario_id == usuario_logado.id,
        Tarefa.concluido == True
    )
    concluidas = session.exec(query_concluidas).one()
    
    pendentes = total - concluidas
    porcentagem = (concluidas / total * 100) if total > 0 else 0

    return {
        "total_tarefas": total,
        "tarefas_concluidas": concluidas,
        "tarefas_pendentes": pendentes,
        "porcentagem_progresso": round(porcentagem, 2)
    }

@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(
    tarefa_id: int,
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    tarefa_db = session.get(Tarefa, tarefa_id)
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if tarefa_db.usuario_id != usuario_logado.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    session.delete(tarefa_db)
    session.commit()
    return {"message": "Tarefa deletada com sucesso"}