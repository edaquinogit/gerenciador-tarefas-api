from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gerenciador de Tarefas API"
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    SESSION_HOURS: int = Field(default=12, ge=1, le=24)
    SESSION_COOKIE_SECURE: bool = False
    BROWSER_ORIGINS: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
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

    @field_validator("BROWSER_ORIGINS")
    @classmethod
    def exact_origins(cls, values):
        from urllib.parse import urlsplit

        for value in values:
            url = urlsplit(value)
            if (
                url.scheme not in ("http", "https")
                or not url.hostname
                or "*" in value
                or url.path
                or url.query
                or url.fragment
                or url.username
            ):
                raise ValueError("BROWSER_ORIGINS exige origens exatas, sem caminho ou curinga")
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()
