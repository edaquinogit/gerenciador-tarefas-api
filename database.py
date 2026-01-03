from sqlmodel import create_engine, Session

sqlite_url = "sqlite:///database.db"


engine = create_engine(sqlite_url)


def get_session():
    with Session(engine) as session:
        yield session