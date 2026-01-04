from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient 
from main import app, obter_usuario_atual
from database import get_session  
from models import Usuario


engine_teste = create_engine("sqlite:///banco_teste.db")
client = TestClient(app)


usuario_teste = Usuario(id=1, username="testador", email="teste@teste.com", password_hash="123")


def fake_get_session():
    """Força o FastAPI a usar o banco de teste"""
    with Session(engine_teste) as session:
        yield session

def fake_obter_usuario_atual():
    """Simula um usuário já logado"""
    return usuario_teste


app.dependency_overrides[get_session] = fake_get_session
app.dependency_overrides[obter_usuario_atual] = fake_obter_usuario_atual


def setup_module():
    """Cria as tabelas no banco de teste antes de rodar os testes"""
    SQLModel.metadata.create_all(engine_teste)


def test_criar_tarefa_vinculada_ao_usuario():
    dados_tarefa = {
        "titulo": "Finalizar testes da API",
        "prioridade": "alta"
    }

    response = client.post("/tarefas", json=dados_tarefa)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["titulo"] == dados_tarefa["titulo"]
    
    assert data["usuario_id"] == usuario_teste.id