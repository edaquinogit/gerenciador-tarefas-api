from datetime import datetime

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from backend.models.ordem import now_utc


class Notificacao(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("evento_id", "usuario_id"),
        Index("ix_notificacao_usuario_lida", "usuario_id", "lida_em"),
    )
    id: int | None = Field(default=None, primary_key=True)
    evento_id: int = Field(foreign_key="eventoordem.id")
    ordem_id: int = Field(foreign_key="ordem.id")
    usuario_id: int = Field(foreign_key="usuario.id")
    mensagem: str
    criado_em: datetime = Field(default_factory=now_utc)
    lida_em: datetime | None = None
