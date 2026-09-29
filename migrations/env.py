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
    try:
        with engine.connect() as connection:
            if connection.dialect.name == "sqlite":
                # SQLite exige reconstrução da tabela para alterar nulabilidade.
                # API parada: desligar FKs só nesta conexão, fora da transação;
                # DDL e verificação de integridade permanecem atômicos.
                connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
                connection.commit()
                try:
                    with connection.begin():
                        connection.exec_driver_sql("BEGIN")
                        context.configure(
                            connection=connection,
                            target_metadata=target_metadata,
                            compare_type=True,
                            transactional_ddl=True,
                        )
                        with context.begin_transaction():
                            context.run_migrations()
                        if connection.exec_driver_sql("PRAGMA foreign_key_check").first():
                            raise RuntimeError("Migração recusada: referências inválidas no banco")
                finally:
                    connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                    connection.commit()
            else:
                context.configure(
                    connection=connection, target_metadata=target_metadata, compare_type=True
                )
                with context.begin_transaction():
                    context.run_migrations()
    finally:
        engine.dispose()
