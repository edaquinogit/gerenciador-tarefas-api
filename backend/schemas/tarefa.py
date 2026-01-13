from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    prioridade: str

    usuario_id: int = Field(
        foreign_key="usuario.id",
        nullable=False,
        sa_column_kwargs={"ondelete": "CASCADE"}
    )

    usuario: "Usuario" = Relationship(back_populates="tarefas")

from .usuario import Usuario
