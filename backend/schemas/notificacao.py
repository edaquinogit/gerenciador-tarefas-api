from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_validator


class NotificacaoRead(BaseModel):
    id: int
    ordem_id: int
    mensagem: str
    criado_em: datetime
    lida_em: datetime | None
    situacao: Literal["AGUARDANDO_COLETA", "COLETADA", "CANCELADA", "EM_PRODUCAO"]

    @field_validator("criado_em", "lida_em", mode="after")
    @classmethod
    def utc(cls, value: datetime | None):
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class CaixaAvisos(BaseModel):
    nao_lidas: int
    itens: list[NotificacaoRead]
