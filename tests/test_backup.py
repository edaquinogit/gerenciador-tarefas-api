import sqlite3

import pytest

from backend.scripts.backup_sqlite import criar_backup


def test_backup_can_be_restored_without_overwriting_previous_backup(tmp_path):
    path = tmp_path / "original com espaço.db"
    source = sqlite3.connect(path)
    source.execute("PRAGMA journal_mode=WAL")
    source.execute("CREATE TABLE exemplo (valor TEXT)")
    source.execute("INSERT INTO exemplo VALUES ('preservado')")
    source.commit()
    first = criar_backup(f"sqlite:///{path}", tmp_path / "backups")
    second = criar_backup(f"sqlite:///{path}", tmp_path / "backups")
    assert first != second and first.is_file()
    source.execute("DELETE FROM exemplo")
    source.commit()
    source.close()
    restored = sqlite3.connect(first)
    try:
        assert restored.execute("SELECT valor FROM exemplo").fetchall() == [("preservado",)]
        assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    finally:
        restored.close()


def test_backup_missing_source_never_creates_empty_database(tmp_path):
    missing = tmp_path / "missing.db"
    with pytest.raises(ValueError):
        criar_backup(f"sqlite:///{missing}", tmp_path / "backups")
    assert not missing.exists()
    for url in ("sqlite://", "sqlite:///:memory:", "postgresql://localhost/example"):
        with pytest.raises(ValueError):
            criar_backup(url, tmp_path / "backups")
