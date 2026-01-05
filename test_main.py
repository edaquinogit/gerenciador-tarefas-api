from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient 
from main import app, obter_usuario_atual
from database import get_session  
from models import Usuario, Tarefa, Prioridade
import pytest


engine_teste = create_engine(
    "sqlite:///banco_teste.db", 
    connect_args={"check_same_thread": False}
)
client = TestClient(app)


@pytest.fixture(autouse=True)
def limpar_banco():
    """Limpa todas as tabelas antes de cada teste individual"""
    SQLModel.metadata.drop_all(engine_teste)
    SQLModel.metadata.create_all(engine_teste)
    yield


usuario_teste = Usuario(id=1, username="testador", email="teste@teste.com", password_hash="123")

def fake_get_session():
    with Session(engine_teste) as session:
        yield session

def fake_obter_usuario_atual():
    return usuario_teste

app.dependency_overrides[get_session] = fake_get_session
app.dependency_overrides[obter_usuario_atual] = fake_obter_usuario_atual


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

def test_usuario_nao_pode_deletar_tarefa_de_outro():
    with Session(engine_teste) as session:
        tarefa_alheia = Tarefa(
            titulo="Tarefa de Outro", 
            prioridade="alta", 
            usuario_id=99 
        )
        session.add(tarefa_alheia)
        session.commit()
        session.refresh(tarefa_alheia)
        id_da_tarefa = tarefa_alheia.id 

    response = client.delete(f"/tarefas/{id_da_tarefa}")
    assert response.status_code == 403

def test_obter_estatisticas_sucesso():
    with Session(engine_teste) as session:
        
        t1 = Tarefa(titulo="T1", concluido=True, usuario_id=1, prioridade=Prioridade.MEDIA)
        t2 = Tarefa(titulo="T2", concluido=True, usuario_id=1, prioridade=Prioridade.ALTA)
        t3 = Tarefa(titulo="T3", concluido=False, usuario_id=1, prioridade=Prioridade.BAIXA)
        t4 = Tarefa(titulo="T4", concluido=False, usuario_id=1, prioridade=Prioridade.BAIXA)
        
        session.add_all([t1, t2, t3, t4])
        session.commit()

    response = client.get("/tarefas/estatisticas")
    data = response.json()

    
    assert response.status_code == 200
    assert data["total_tarefas"] == 4
    assert data["tarefas_concluidas"] == 2
    assert data["tarefas_pendentes"] == 2
    assert data["porcentagem_progresso"] == 50.0