from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Projeto
    PROJECT_NAME: str = "Gerenciador de Tarefas API"

    # Segurança
    SECRET_KEY: str = "chave-super-secreta-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Banco de dados
    DATABASE_URL: str = "sqlite:///database.db"

    # API (opcional, se você usa no frontend/deploy)
    API_URL: str | None = None

    # Configuração do Pydantic v2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# 👉 objeto global que será importado
settings = Settings()