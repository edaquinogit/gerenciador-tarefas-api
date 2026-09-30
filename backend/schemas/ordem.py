from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoriaOrdem = Literal["ROUPA_DE_CAMA", "BANHO", "COZINHA", "CORTINA", "ALMOFADA", "OUTROS"]

StatusOrdem = Literal["PENDENTE", "CORTANDO", "COSTURANDO", "PRONTO"]


class OrdemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    produto: str = Field(min_length=1, max_length=150)
    especificacao: str = Field(min_length=1, max_length=500)
    quantidade: int = Field(gt=0, le=1000000, strict=True)
    unidade: Literal["pecas", "kits"] = "pecas"
    prioridade: Literal["NORMAL", "URGENTE"] = "NORMAL"
    prazo: datetime
    observacao: str = Field(default="", max_length=1000)

    @field_validator("prazo")
    @classmethod
    def utc_deadline(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Informe prazo com fuso horário")
        return value.astimezone(timezone.utc).replace(tzinfo=None)


class ComandoOrdem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    versao: int = Field(ge=1, strict=True)


class EtapaUpdate(ComandoOrdem):
    status: Literal["CORTANDO", "COSTURANDO", "PRONTO"]


class Cancelamento(ComandoOrdem):
    motivo: str = Field(min_length=5, max_length=500)


class OrdemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    produto: str
    especificacao: str
    quantidade: int
    unidade: str
    prioridade: str
    prazo: datetime
    observacao: str
    categoria: CategoriaOrdem
    status: StatusOrdem
    solicitante_id: int
    solicitante_nome: str
    responsavel_nome: str | None
    coletado_nome: str | None
    responsavel_id: int | None
    criado_em: datetime
    atualizado_em: datetime
    pronto_em: datetime | None
    coletado_em: datetime | None
    coletado_por: int | None
    cancelado_em: datetime | None
    versao: int

    @field_validator(
        "prazo",
        "criado_em",
        "atualizado_em",
        "pronto_em",
        "coletado_em",
        "cancelado_em",
        mode="after",
    )
    @classmethod
    def aware_utc(cls, value: datetime | None):
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class EventoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    usuario_id: int
    usuario_nome: str
    acao: str
    status_anterior: str | None
    status_novo: str
    motivo: str
    criado_em: datetime
    versao: int

    @field_validator("criado_em", mode="after")
    @classmethod
    def aware_utc(cls, value: datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
