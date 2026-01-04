from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "sua_chave_secreta_super_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def gerar_hash_senha(senha: str):
    return pwd_context.hash(senha)

def verificar_senha(senha_pura: str, senha_hasheada: str):
    try:
        if not senha_hasheada:
            return False
        return pwd_context.verify(senha_pura, senha_hasheada)
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

def criar_token_acesso(dados: dict):
    a_copiar = dados.copy()
 
    expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    a_copiar.update({"exp": expiracao})
    token_jwt = jwt.encode(a_copiar, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt