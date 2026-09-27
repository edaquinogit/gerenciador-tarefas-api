"""Valida o schema legado antes de marcar a baseline, sem recriar tabelas."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from backend.core.config import get_settings
from backend.database.connection import build_engine
from backend.database.legacy import metadata


def main():
    engine = build_engine(get_settings().DATABASE_URL)
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            if tables != {"usuario", "tarefa"}:
                raise SystemExit(
                    "Adoção recusada: esperado banco legado com somente usuario e tarefa, sem alembic_version."
                )
            if compare_metadata(MigrationContext.configure(connection), metadata):
                raise SystemExit(
                    "Adoção recusada: schema diferente da baseline. Revise uma cópia do banco."
                )
            orphan = connection.execute(
                text(
                    "SELECT tarefa.id FROM tarefa LEFT JOIN usuario ON usuario.id = tarefa.usuario_id WHERE usuario.id IS NULL LIMIT 1"
                )
            ).first()
            if orphan:
                raise SystemExit("Adoção recusada: existem tarefas sem usuário válido.")
        command.stamp(Config("alembic.ini"), "0001")
        print("Baseline registrada. Usuários e tarefas preservados.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
