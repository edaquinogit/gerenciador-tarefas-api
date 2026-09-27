from sqlmodel import Field, SQLModel


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    perfil: str = Field(default="FUNCIONARIO")
    setor: str | None = Field(default=None)
    token_version: int = Field(default=0)
