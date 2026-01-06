from sqlmodel import SQLModel, create_engine, Session

# Nome do arquivo de banco que definimos
sqlite_file_name = "banco_producao_v1.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Criamos a conexão (engine)
engine = create_engine(sqlite_url, echo=True)

# Função para as rotas do FastAPI usarem
def get_session():
    with Session(engine) as session:
        yield session

# Função para criar as tabelas
def create_db_and_tabelas():
    # Importamos os modelos aqui dentro para evitar importação circular
    from models import Usuario, Tarefa
    SQLModel.metadata.create_all(engine)