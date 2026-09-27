from sqlmodel import Field, SQLModel


class Tarefa(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    prioridade: str = Field(default="Média")
    concluido: bool = Field(default=False)
    usuario_id: int = Field(foreign_key="usuario.id")
