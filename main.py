from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
from sqlmodel import Session, select
from models import Tarefa, Usuario
from database import get_session, create_db_and_tabelas
from security import verificar_senha, criar_token_acesso, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from sqlalchemy import func

# Configuração do esquema de segurança
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- GERENCIAMENTO DE CICLO DE VIDA (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Cria o banco e as tabelas ao iniciar
    create_db_and_tabelas()
    
    # 2. Obtém a sessão do gerador manualmente para listar usuários
    session_generator = get_session()
    session = next(session_generator) # Extrai a sessão ativa
    
    try:
        usuarios = session.exec(select(Usuario)).all()
        print("\n" + "="*30)
        print("USUÁRIOS CADASTRADOS:")
        if not usuarios:
            print("Nenhum usuário encontrado no banco.")
        for u in usuarios:
            print(f"- Usuário: {u.username}")
        print("="*30 + "\n")
    finally:
        session.close() # Garante o fechamento da conexão
    
    yield  # O servidor fica rodando aqui
    
    print("Desligando o servidor...")

# Inicialização do App com o lifespan corrigido
app = FastAPI(lifespan=lifespan)

# --- DEPENDÊNCIA PARA OBTER USUÁRIO ATUAL ---
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

# --- ROTAS DE AUTENTICAÇÃO ---
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

# --- CRUD DE TAREFAS ---
@app.post("/tarefas")
def criar_tarefa(
    tarefa: Tarefa,
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    try:
        tarefa.usuario_id = usuario_logado.id # Vincula ao dono
        session.add(tarefa)
        session.commit()
        session.refresh(tarefa)
        return tarefa
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=422,
            detail="Erro ao criar tarefa. Verifique os dados."
        )

@app.get("/tarefas")
def listar_tarefas(
    session: Session = Depends(get_session),
    usuario_logado: Usuario = Depends(obter_usuario_atual)
):
    statement = select(Tarefa).where(Tarefa.usuario_id == usuario_logado.id)
    return session.exec(statement).all()

# --- ESTATÍSTICAS ---
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
    concluidas = session.exec