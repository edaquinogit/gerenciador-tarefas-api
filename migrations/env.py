from alembic import context
from sqlmodel import SQLModel

from backend.core.config import get_settings
from backend.database.connection import build_engine
from backend.models import Tarefa, Usuario  # noqa: F401

config = context.config
target_metadata = SQLModel.metadata
url = get_settings().DATABASE_URL

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
