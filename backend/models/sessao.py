from datetime import datetime

from sqlmodel import Field, SQLModel


class Sessao(SQLModel, table=True):
    id: str = Field(primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    token_version: int
    expira_em: datetime
    revogada: bool = False
    cookie_hash: str | None = Field(default=None, unique=True)
    codigo_hash: str | None = Field(default=None, unique=True)
    codigo_expira_em: datetime
    estado: str = "{}"
