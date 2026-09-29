from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Ordem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(unique=True)
    produto: str
    especificacao: str
    quantidade: int
    unidade: str
    prioridade: str
    prazo: datetime
    observacao: str
    categoria: str = Field(default="OUTROS", index=True)
    status: str = Field(default="PENDENTE", index=True)
    solicitante_id: int = Field(foreign_key="usuario.id")
    responsavel_id: int | None = Field(default=None, foreign_key="usuario.id")
    criado_em: datetime = Field(default_factory=now_utc)
    atualizado_em: datetime = Field(default_factory=now_utc)
    pronto_em: datetime | None = None
    coletado_em: datetime | None = None
    coletado_por: int | None = Field(default=None, foreign_key="usuario.id")
    cancelado_em: datetime | None = None
    versao: int = Field(default=1)


class EventoOrdem(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ordem_id", "versao"),)
    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(unique=True)
    ordem_id: int = Field(foreign_key="ordem.id", index=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    usuario_nome: str
    acao: str
    status_anterior: str | None = None
    status_novo: str
    motivo: str = ""
    criado_em: datetime = Field(default_factory=now_utc)
    versao: int
