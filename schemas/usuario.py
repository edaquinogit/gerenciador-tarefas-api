from sqlmodel import SQLModel

class UsuarioCreate(SQLModel):
    username: str
    email: str
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str
