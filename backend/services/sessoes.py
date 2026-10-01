import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlmodel import delete

from backend.core.security import create_access_token
from backend.models import Sessao, Usuario

COOKIE = "gerenciador_sessao"


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def criar(session, user, settings):
    # Remove somente sessões já vencidas, sem afetar registros operacionais.
    session.exec(delete(Sessao).where(Sessao.expira_em < now()))
    code = secrets.token_urlsafe(32)
    record = Sessao(
        id=str(uuid4()),
        usuario_id=user.id,
        token_version=user.token_version,
        expira_em=now() + timedelta(hours=settings.SESSION_HOURS),
        codigo_hash=digest(code),
        codigo_expira_em=now() + timedelta(minutes=2),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record, code


def validar(session, record):
    user = session.get(Usuario, record.usuario_id) if record else None
    if (
        not record
        or record.revogada
        or record.expira_em <= now()
        or not user
        or not user.is_active
        or record.token_version != user.token_version
    ):
        raise HTTPException(401, "Sessão encerrada. Entre novamente.")
    return user


def apresentar(record, user, settings):
    return {
        "access_token": create_access_token(user.username, settings, user.token_version, record.id),
        "expires_at": record.expira_em.replace(tzinfo=timezone.utc).isoformat(),
        "refresh_seconds": min(300, max(5, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 30)),
        "state": json.loads(record.estado),
    }
