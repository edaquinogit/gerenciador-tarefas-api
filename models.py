from sqlmodel import SQLModel, Field, create_engine, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum



class Prioridade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    password_hash: str
    is_active: bool = Field(default=True)

    tarefas: list["Tarefa"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Tarefa(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    prioridade: str
    concluido: bool = False

    usuario_id: int | None = Field(default=None, foreign_key="usuario.id")

    usuario: Optional[Usuario] = Relationship(back_populates="tarefas")

def crie_o_banco():
    from database import engine
    SQLModel.metadata.create_all(engine)