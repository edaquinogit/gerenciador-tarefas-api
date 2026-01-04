from sqlmodel import SQLModel, create_engine, Session


sqlite_file_name = "banco_producao_v1.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tabelas():
    from models import Usuario, Tarefa
    SQLModel.metadata.create_all(engine)