from fastapi import Request
from sqlalchemy import event
from sqlmodel import Session, create_engine


def build_engine(database_url: str, **kwargs):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        **kwargs,
    )
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


def get_session(request: Request):
    with Session(request.app.state.engine) as session:
        yield session
