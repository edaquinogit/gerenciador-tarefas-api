from sqlmodel import SQLModel

class TarefaCreate(SQLModel):
    titulo: str
    prioridade: str
