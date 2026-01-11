import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient

from main import app
from database.connection import get_session
from database.models import Usuario, Tarefa
from core.security import get_current_user

# -------------------------------------------------
# BANCO DE TESTE
# -------------------------------------------------

engine_test = create_engine(
    "sqlite:///./banco_teste.db",
    connect_args={"check_same_thread": False},
)

client = TestClient(app)

# -------------------------------------------------
# FIXTURES
# -------------------------------------------------

@pytest.fixture(autouse=True)
def limpar_banco():
    SQLModel.metadata.drop_all(engine_test)
    SQLModel.metadata.create_all(engine_test)
    yield


@pytest.fixture
def session():
    with Session(engine_test) as session:
        yield session


# -------------------------------------------------
# DEPENDENCY OVERRIDES
# -------------------------------------------------

usuario_teste = Usuario(
    id=1,
    username="testador",
    email="teste@teste.com",
    password_hash="fake-hash",
    is_active=True,
    is_admin=False,
)

def fake_get_session():
    with Session(engine_test) as session:
        yield session


def fake_get_current_user():
    return usuario_teste


app.dependency_overrides[get_session] = fake_get_session
app.dependency_overrides[get_current_user] = fake_get_current_user

# -------------------------------------------------
# TESTES
# -------------------------------------------------

def test_criar_tarefa_vinculada_ao_usuario():
    dados = {
        "titulo": "Finalizar testes",
        "prioridade": "alta",
    }

    response = client.post("/tarefas", json=dados)

    assert response.status_code == 200
    assert response.json()["usuario_id"] == usuario_teste.id


def test_usuario_nao_pode_deletar_tarefa_de_outro():
    with Session(engine_test) as session:
        tarefa = Tarefa(
            titulo="Tarefa alheia",
            prioridade="alta",
            usuario_id=999,
        )
        session.add(tarefa)
        session.commit()
        session.refresh(tarefa)

    response = client.delete(f"/tarefas/{tarefa.id}")

    assert response.status_code == 404


def test_delete_usuario_nao_deixa_tarefa_orfa(session: Session):
    usuario = Usuario(
        username="teste",
        email="teste@teste.com",
        password_hash="123",
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    tarefa = Tarefa(
        titulo="Tarefa vinculada",
        prioridade="media",
        usuario_id=usuario.id,
    )
    session.add(tarefa)
    session.commit()

    session.delete(usuario)
    session.commit()

    tarefa_depois = session.get(Tarefa, tarefa.id)
    assert tarefa_depois is None
