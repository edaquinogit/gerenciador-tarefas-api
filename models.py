from sqlmodel import SQLModel, Field
from typing import Optional
from database import engine


class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(min_length=3, max_length=50)
    concluida: bool = False

def crie_o_banco():
    SQLModel.metadata.create_all(engine)