from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import event
from sqlmodel import Session, SQLModel, select

from backend.database.connection import build_engine
from backend.models import Usuario
from backend.models.ordem import EventoOrdem, Ordem
from backend.schemas.ordem import EtapaUpdate, OrdemCreate
from backend.services import ordens
from tests.test_ordens import payload


def prepare(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'concorrencia.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = Usuario(
            username="admin", email="admin@example.com", password_hash="unused", perfil="ADMIN"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        ordem = ordens.criar(session, OrdemCreate(**payload()), user)
        ident, user_id = ordem.id, user.id
    return engine, ident, user_id


def test_two_simultaneous_updates_only_one_wins(tmp_path):
    engine, ident, user_id = prepare(tmp_path)

    def change():
        with Session(engine) as session:
            user = session.get(Usuario, user_id)
            try:
                ordens.executar(
                    session,
                    ident,
                    EtapaUpdate(request_id=uuid4(), versao=1, status="CORTANDO"),
                    user,
                    "ETAPA",
                    destino="CORTANDO",
                )
                return 200
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: change(), range(2)))
    assert sorted(outcomes) == [200, 409]
    with Session(engine) as session:
        assert session.get(Ordem, ident).versao == 2
        assert len(session.exec(select(EventoOrdem)).all()) == 2
    engine.dispose()


def test_history_failure_rolls_back_status(tmp_path):
    engine, ident, user_id = prepare(tmp_path)

    def fail_history(mapper, connection, target):
        raise RuntimeError("simulated storage failure")

    event.listen(EventoOrdem, "before_insert", fail_history)
    try:
        with Session(engine) as session:
            with pytest.raises(RuntimeError):
                ordens.executar(
                    session,
                    ident,
                    EtapaUpdate(request_id=uuid4(), versao=1, status="CORTANDO"),
                    session.get(Usuario, user_id),
                    "ETAPA",
                    destino="CORTANDO",
                )
    finally:
        event.remove(EventoOrdem, "before_insert", fail_history)
    with Session(engine) as session:
        ordem = session.get(Ordem, ident)
        assert ordem.status == "PENDENTE" and ordem.versao == 1
        assert len(session.exec(select(EventoOrdem)).all()) == 1
    engine.dispose()
