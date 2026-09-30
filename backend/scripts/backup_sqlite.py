"""Cria uma cópia consistente do SQLite configurado, sem sobrescrever backups."""

import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url

from backend.core.config import get_settings


def criar_backup(database_url: str, directory: Path) -> Path:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Este comando exige um banco SQLite em arquivo.")
    source = Path(url.database).resolve()
    if not source.is_file():
        raise ValueError("Banco configurado não encontrado; nenhuma base nova foi criada.")
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"database-{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}.bak"
    connection = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise ValueError("Banco com erro de integridade. Migração não deve ser executada.")
        with destination.open("xb"):
            pass
        target = sqlite3.connect(destination)
        try:
            connection.backup(target)
        finally:
            target.close()
    finally:
        connection.close()
    return destination


def main():
    try:
        result = criar_backup(get_settings().DATABASE_URL, Path("backups"))
    except (ValueError, OSError, sqlite3.Error):
        raise SystemExit(
            "Backup não concluído. Confira .env, banco SQLite existente, permissões e espaço. "
            "Não prossiga com a migração."
        ) from None
    print(f"Backup concluído: {result.resolve()}")


if __name__ == "__main__":
    main()
