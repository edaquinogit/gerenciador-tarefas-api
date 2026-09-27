from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TarefaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    titulo: str = Field(min_length=1, max_length=200)
    prioridade: Literal["Baixa", "Média", "Alta"] = "Média"


class TarefaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    prioridade: str
    concluido: bool
    usuario_id: int
