from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Setor = Literal["SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"]
Perfil = Literal["ADMIN", "FUNCIONARIO"]


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha deve ter no máximo 72 bytes em UTF-8")
        return value

    @field_validator("email")
    @classmethod
    def basic_email(cls, value: str) -> str:
        value = value.strip().lower()
        if value.count("@") != 1 or not all(value.split("@")):
            raise ValueError("E-mail inválido")
        return value


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    is_active: bool
    perfil: Perfil
    setor: Setor | None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FuncionarioCreate(UsuarioCreate):
    setor: Setor


class FuncionarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setor: Setor
    is_active: bool


class SenhaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, value: str) -> str:
        return UsuarioCreate.bcrypt_limit(value)


class MinhaSenhaUpdate(SenhaUpdate):
    current_password: str
