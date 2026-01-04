from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
from sqlmodel import Session, select
from models import Tarefa, Prioridade, Usuario
from database import get_session, create_db_and_tabelas
from security import gerar_hash_senha, verificar_senha, criar_token_acesso 
from jose import JWTError, jwt
from security import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tabelas()
    yield

app = FastAPI(lifespan=lifespan)

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


@app.post("/tarefas")
def criar_tarefa(
    tarefa: Tarefa, 
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual) 
):
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.get("/tarefas")
def listar_tarefas(
    session: Session = Depends(get_session), 
    concluida: bool = None,
    termo: str = None,
    prioridade: Prioridade = None,
    usuario_logado: Usuario = Depends(obter_usuario_atual) 
):
    statement = select(Tarefa)
    
    if concluida is not None:
        statement = statement.where(Tarefa.concluida == concluida)
    
    if termo:
        statement = statement.where(Tarefa.titulo.contains(termo))
        
    if prioridade:
        statement = statement.where(Tarefa.prioridade == prioridade)
    
    tarefas = session.exec(statement).all()
    return tarefas

@app.patch("/tarefas/{tarefa_id}")
def atualizar_tarefa(
    tarefa_id: int, 
    novo_titulo: str = None,
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual) # <--- Protegido!
):
    tarefa_no_banco = session.get(Tarefa, tarefa_id)

    if not tarefa_no_banco:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    if novo_titulo:
        tarefa_no_banco.titulo = novo_titulo

    tarefa_no_banco.concluida = True
    
    session.add(tarefa_no_banco)
    session.commit()
    session.refresh(tarefa_no_banco)
    
    return tarefa_no_banco

@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(
    tarefa_id: int, 
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual) # <--- Protegido!
):
    tarefa = session.get(Tarefa, tarefa_id)

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    session.delete(tarefa)
    session.commit()

    return {"mensagem": "Deletado com sucesso!"}

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