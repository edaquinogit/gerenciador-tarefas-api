import pytest
from pydantic import ValidationError

from backend.core.config import Settings
from backend.core.security import get_password_hash, verify_password
from backend.schemas.usuario import UsuarioCreate


def test_missing_secret_fails(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_weak_secret_fails():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, SECRET_KEY="curta")


def test_registration_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_REGISTRATION", raising=False)
    assert not Settings(
        _env_file=None, SECRET_KEY="test-key-longer-than-thirty-two-characters"
    ).ALLOW_REGISTRATION


def test_legacy_bcrypt_compatibility():
    hashed = get_password_hash("senha-existente")
    assert hashed.startswith("$2b$")
    assert verify_password("senha-existente", hashed)
    assert not verify_password("outra", hashed)


def test_password_byte_limit():
    with pytest.raises(ValidationError):
        UsuarioCreate(username="teste", telefone="79999990001", password="á" * 37)
