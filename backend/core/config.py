from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Projeto
    PROJECT_NAME: str = "Gerenciador de Tarefas API"

    # Segurança
    SECRET_KEY: str = "chave-super-secreta-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Banco de dados
    DATABASE_URL: str = "sqlite:///database.db"

    class Config:
        env_file = ".env"


# 👉 objeto global que será importado
settings = Settings()
