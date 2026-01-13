from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    tarefas: List["Tarefa"] = Relationship(back_populates="usuario")

class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    prioridade: str = Field(default="Média")
    concluido: bool = Field(default=False)
    usuario_id: int = Field(foreign_key="usuario.id")
    usuario: Optional["Usuario"] = Relationship(back_populates="tarefas")

class UsuarioCreate(SQLModel):
    username: str
    email: str
    password: str

class TarefaCreate(SQLModel):
    titulo: str
    prioridade: Optional[str] = "Média"

class Token(SQLModel):
    access_token: str
    token_type: str