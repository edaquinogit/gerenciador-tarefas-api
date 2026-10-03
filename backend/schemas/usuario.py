from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from shared.telefone import normalizar_telefone

Telefone = Annotated[str, Field(max_length=32), AfterValidator(normalizar_telefone)]

Setor = Literal["SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"]
Perfil = Literal["ADMIN", "FUNCIONARIO"]


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    telefone: Telefone
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha deve ter no máximo 72 bytes em UTF-8")
        return value


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    telefone: str | None
    is_active: bool
    perfil: Perfil
    setor: Setor | None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    browser_code: str | None = None
    session_id: str | None = None


class FuncionarioCreate(UsuarioCreate):
    setor: Setor


class FuncionarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setor: Setor
    is_active: bool
    telefone: Telefone | None = None

    @field_validator("telefone")
    @classmethod
    def telefone_informado(cls, value):
        if value is None:
            raise ValueError("Informe o telefone ou omita o campo para mantê-lo")
        return value


class MeuTelefoneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    telefone: Telefone


class SenhaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, value: str) -> str:
        return UsuarioCreate.bcrypt_limit(value)


class MinhaSenhaUpdate(SenhaUpdate):
    current_password: str


class DecisaoSenha(BaseModel):
    model_config = ConfigDict(extra="forbid")
    permitir: bool
    versao: int = Field(ge=1)
