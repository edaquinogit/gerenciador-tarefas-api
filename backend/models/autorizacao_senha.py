from datetime import datetime

from sqlmodel import Field, SQLModel


class AutorizacaoSenha(SQLModel, table=True):
    usuario_id: int = Field(primary_key=True, foreign_key="usuario.id")
    status: str = Field(default="PENDENTE")
    solicitado_em: datetime
    decidido_em: datetime | None = None
    expira_em: datetime | None = None
    consumido_em: datetime | None = None
    admin_id: int | None = Field(default=None, foreign_key="usuario.id")
    versao: int = Field(default=1)
