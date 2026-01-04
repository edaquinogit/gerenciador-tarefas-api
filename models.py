from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from datetime import datetime
from enum import Enum



class Prioridade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"

class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    concluida: bool = Field(default=False)

    criado_em: datetime = Field(default_factory=datetime.now)

    prioridade: Prioridade = Field(default=Prioridade.MEDIA)


def crie_o_banco():
    from database import engine
    SQLModel.metadata.create_all(engine)