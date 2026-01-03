from sqlmodel import create_engine, Session

# Nome do arquivo do banco de dados
sqlite_file_name = "database.db"
# URL de conexão para o SQLite
sqlite_url = f"sqlite:///{sqlite_file_name}"

# O objeto 'engine' que o models.py está procurando
engine = create_engine(sqlite_url, echo=True)

# Função para fornecer a sessão para as rotas da API
def get_session():
    with Session(engine) as session:
        yield session