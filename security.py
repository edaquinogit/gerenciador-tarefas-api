import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from database import get_session
from models import Usuario
import os

# --- CONFIGURAÇÕES DE SEGURANÇA ---
SECRET_KEY = "sua_chave_secreta_super_protegida_aqui" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define onde a API deve buscar o Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- FUNÇÕES DE SENHA (VERSÃO CORRIGIDA SEM PASSLIB) ---

def gerar_hash_senha(senha: str) -> str:
    """Gera hash usando bcrypt diretamente para evitar erros de versão."""
    salt = bcrypt.gensalt()
    # Transforma a senha em bytes, gera o hash e converte de volta para string
    hash_bytes = bcrypt.hashpw(senha.encode('utf-8'), salt)
    return hash_bytes.decode('utf-8')

def verificar_senha(senha_limpa: str, senha_hash: str) -> bool:
    """Compara a senha limpa com o hash do banco usando bcrypt."""
    try:
        return bcrypt.checkpw(
            senha_limpa.encode('utf-8'), 
            senha_hash.encode('utf-8')
        )
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

# --- FUNÇÕES DE TOKEN (JWT) ---

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- FUNÇÃO DE VALIDAÇÃO ---

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if user is None:
        raise credentials_exception
    return user

# --- FUNÇÃO DE AUTENTICAÇÃO ---

def authenticate_user(session: Session, username: str, password_limpa: str):
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if not user:
        print(f"❌ Usuário {username} não encontrado no banco!")
        return False
    
    batem = verificar_senha(password_limpa, user.password_hash)
    print(f"🔍 Tentativa de Login: {username} | Senha bate? {batem}")
    
    if not batem:
        return False
    return user