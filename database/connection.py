from sqlmodel import SQLModel, create_engine, Session
import os

# -------------------------
# URL do banco
# -------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///database.db"  # padrão local
)

# -------------------------
# Engine
# -------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)

# -------------------------
# Sessão (Dependency Injection)
# -------------------------
def get_session():
    with Session(engine) as session:
        yield session
