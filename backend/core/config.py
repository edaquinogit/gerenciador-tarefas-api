from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gerenciador de Tarefas API"
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    DATABASE_URL: str = "sqlite:///database.db"
    CORS_ORIGINS: list[str] = []
    ALLOW_REGISTRATION: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("ALGORITHM")
    @classmethod
    def supported_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Use HS256 nesta versão")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
