from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient 
from main import app, obter_usuario_atual
from database import get_session  
from models import Usuario, Tarefa, Prioridade
import pytest

# 1. Configuração do Banco de Testes 🗄️
engine_teste = create_engine(
    "sqlite:///banco_teste.db", 
    connect_args={"check_same_thread": False}
)
client = TestClient(app)

# 2. Fixtures (Os "Ajudantes" do Pytest) 
@pytest.fixture(autouse=True)
def limpar_banco():
    """Limpa todas as tabelas antes de cada teste individual"""
    SQLModel.metadata.drop_all(engine_teste)
    SQLModel.metadata.create_all(engine_teste)
    yield

@pytest.fixture
def session():
    """Fornece uma sessão ativa para os testes que precisarem tocar no banco diretamente"""
    with Session(engine_teste) as session:
        yield session

# 3. Mocks e Overrides (Simulações) 
usuario_teste = Usuario(id=1, username="testador", email="teste@teste.com", password_hash="123")

def fake_get_session():
    with Session(engine_teste) as session:
        yield session

def fake_obter_usuario_atual():
    return usuario_teste

app.dependency_overrides[get_session] = fake_get_session
app.dependency_overrides[obter_usuario_atual] = fake_obter_usuario_atual

# 4. Seus Testes 🧪

def test_criar_tarefa_vinculada_ao_usuario():
    dados_tarefa = {"titulo": "Finalizar testes", "prioridade": "alta"}
    response = client.post("/tarefas", json=dados_tarefa)
    assert response.status_code == 200
    assert response.json()["usuario_id"] == usuario_teste.id

def test_usuario_nao_pode_deletar_tarefa_de_outro():
    with Session(engine_teste) as session:
        tarefa_alheia = Tarefa(titulo="Alheia", prioridade="alta", usuario_id=99)
        session.add(tarefa_alheia)
        session.commit()
        session.refresh(tarefa_alheia)
        id_da_tarefa = tarefa_alheia.id 

    response = client.delete(f"/tarefas/{id_da_tarefa}")
    assert response.status_code == 403

def test_delete_usuario_cascade_tarefas(session: Session):
    """Teste principal: Deletar usuário deve deletar suas tarefas automaticamente 💣"""
    # Criar o usuário
    usuario = Usuario(username="testedelete", email="delete@test.com", password_hash="123")
    session.add(usuario)
    session.commit()

    # Criar a tarefa vinculada
    tarefa = Tarefa(titulo="Tarefa Orfã", prioridade="Baixa", usuario_id=usuario.id)
    session.add(tarefa)
    session.commit()

    # Deletar o usuário
    session.delete(usuario)
    session.commit()

    # Verificar se a tarefa sumiu (Cascade!)
    tarefa_apos_delete = session.get(Tarefa, tarefa.id)
    assert tarefa_apos_delete is None