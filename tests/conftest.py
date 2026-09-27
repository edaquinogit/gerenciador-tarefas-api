import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from backend.core.config import Settings
from backend.database.connection import build_engine
from backend.main import create_app


@pytest.fixture
def client():
    engine = build_engine("sqlite://", poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    settings = Settings(
        _env_file=None,
        SECRET_KEY="test-only-key-that-is-at-least-32-chars",
        ALLOW_REGISTRATION=True,
    )
    with TestClient(create_app(settings, engine)) as client:
        yield client
    engine.dispose()


@pytest.fixture
def user_factory(client):
    def create(username="funcionario"):
        response = client.post(
            "/usuarios",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "senha-segura-123",
            },
        )
        assert response.status_code == 201
        token = client.post(
            "/token", data={"username": username, "password": "senha-segura-123"}
        ).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return create
