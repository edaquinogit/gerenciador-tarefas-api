from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database.connection import get_session
from database.models import Usuario

# =========================
# OAUTH2
# =========================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# =========================
# SENHAS (bcrypt)
# =========================

def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def verificar_senha(senha_limpa: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(
        senha_limpa.encode("utf-8"),
        senha_hash.encode("utf-8")
    )

# =========================
# JWT
# =========================

def criar_token_acesso(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =========================
# USUÁRIO LOGADO
# =========================

def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Usuario:

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise credenciais_invalidas
    except JWTError:
        raise credenciais_invalidas

    usuario = session.exec(
        select(Usuario).where(Usuario.username == username)
    ).first()

    if not usuario or not usuario.is_active:
        raise credenciais_invalidas

    return usuario

# =========================
# AUTENTICAÇÃO
# =========================

def autenticar_usuario(
    session: Session,
    username: str,
    password: str
) -> Usuario | None:

    usuario = session.exec(
        select(Usuario).where(Usuario.username == username)
    ).first()

    if not usuario:
        return None

    if not verificar_senha(password, usuario.password_hash):
        return None

    return usuario
