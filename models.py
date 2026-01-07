from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

# --- MODELOS DE TABELA (BANCO DE DADOS) ---

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str
    password_hash: str
    is_active: bool = True
    is_admin: bool = Field(default=False)
    
    # Relacionamento: Um usuário tem várias tarefas
    tarefas: List["Tarefa"] = Relationship(back_populates="usuario")

class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    prioridade: str
    concluido: bool = Field(default=False)
    
    # Chave estrangeira para o usuário
    usuario_id: int = Field(foreign_key="usuario.id")
    usuario: Optional[Usuario] = Relationship(back_populates="tarefas")

# --- MODELOS DE DADOS (PARA VALIDAÇÃO/API) ---

class UsuarioCreate(SQLModel):
    username: str
    email: str
    password: str  # Senha pura que vem do formulário

class TarefaCreate(SQLModel):
    titulo: str
    prioridade: str

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None