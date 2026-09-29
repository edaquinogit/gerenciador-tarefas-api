from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from backend.core.config import Settings
from backend.database.connection import get_session
from backend.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Senha excede o limite de 72 bytes")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if len(password.encode("utf-8")) > 72:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


DUMMY_HASH = get_password_hash("dummy-password-never-used")


def authenticate_user(session: Session, username: str, password: str) -> Usuario | None:
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    return user if user and user.is_active and valid else None


def create_access_token(username: str, settings: Settings, token_version: int = 0) -> str:
    return jwt.encode(
        {
            "sub": username,
            "ver": token_version,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    error = HTTPException(
        401, "Credenciais inválidas ou expiradas", headers={"WWW-Authenticate": "Bearer"}
    )
    settings = request.app.state.settings
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        username = payload["sub"]
        if not isinstance(username, str) or not username:
            raise error
    except JWTError:
        raise error from None
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if (
        not user
        or not user.is_active
        or type(payload.get("ver")) is not int
        or payload["ver"] != user.token_version
    ):
        raise error
    return user


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.perfil != "ADMIN":
        raise HTTPException(403, "Somente o administrador pode gerenciar funcionários")
    return user
