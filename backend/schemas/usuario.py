from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str

    tarefas: List["Tarefa"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

from .tarefa import Tarefa
