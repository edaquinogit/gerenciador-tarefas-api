from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update

from backend.models.autorizacao_senha import AutorizacaoSenha
from backend.models.ordem import now_utc
from backend.models.usuario import Usuario


def apresentar(item):
    if item is None:
        return {"status": "NAO_SOLICITADA", "versao": 0, "expira_em": None}
    data = item.model_dump()
    if item.status == "AUTORIZADA" and item.expira_em <= now_utc():
        data["status"] = "EXPIRADA"
    for key in ("solicitado_em", "decidido_em", "expira_em", "consumido_em"):
        data[key] = data[key].isoformat() + "Z" if data[key] else None
    return data


def consultar(session, user):
    return apresentar(session.get(AutorizacaoSenha, user.id))


def solicitar(session: Session, user: Usuario):
    if user.perfil == "ADMIN":
        raise HTTPException(400, "Administradores não precisam solicitar autorização")
    item = session.get(AutorizacaoSenha, user.id)
    if apresentar(item)["status"] in {"PENDENTE", "AUTORIZADA"}:
        return apresentar(item)
    try:
        if item is None:
            session.add(AutorizacaoSenha(usuario_id=user.id, solicitado_em=now_utc()))
        else:
            result = session.exec(
                update(AutorizacaoSenha)
                .where(
                    AutorizacaoSenha.usuario_id == user.id, AutorizacaoSenha.versao == item.versao
                )
                .values(
                    status="PENDENTE",
                    solicitado_em=now_utc(),
                    decidido_em=None,
                    expira_em=None,
                    consumido_em=None,
                    admin_id=None,
                    versao=AutorizacaoSenha.versao + 1,
                )
            )
            if result.rowcount != 1:
                raise HTTPException(409, "Solicitação alterada. Atualize e tente novamente.")
        session.commit()
    except IntegrityError:
        session.rollback()
    session.expire_all()
    return consultar(session, user)


def listar(session):
    rows = session.exec(
        select(AutorizacaoSenha, Usuario)
        .join(Usuario, Usuario.id == AutorizacaoSenha.usuario_id)
        .where(Usuario.perfil == "FUNCIONARIO", Usuario.is_active.is_(True))
        .order_by(AutorizacaoSenha.solicitado_em.desc())
    ).all()
    return [{**apresentar(item), "username": user.username} for item, user in rows]


def decidir(session, usuario_id, admin, permitir, versao):
    user = session.get(Usuario, usuario_id)
    if not user or user.perfil != "FUNCIONARIO" or not user.is_active:
        raise HTTPException(404, "Funcionário ativo não encontrado")
    now = now_utc()
    result = session.exec(
        update(AutorizacaoSenha)
        .where(
            AutorizacaoSenha.usuario_id == usuario_id,
            AutorizacaoSenha.versao == versao,
            AutorizacaoSenha.status.in_(["PENDENTE", "AUTORIZADA"]),
        )
        .values(
            status="AUTORIZADA" if permitir else "RECUSADA",
            decidido_em=now,
            expira_em=now + timedelta(minutes=30) if permitir else None,
            admin_id=admin.id,
            versao=AutorizacaoSenha.versao + 1,
        )
    )
    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "Solicitação alterada. Atualize o painel.")
    session.commit()
    return consultar(session, user)


def consumir(session, user):
    if user.perfil == "ADMIN":
        return
    result = session.exec(
        update(AutorizacaoSenha)
        .where(
            AutorizacaoSenha.usuario_id == user.id,
            AutorizacaoSenha.status == "AUTORIZADA",
            AutorizacaoSenha.expira_em > now_utc(),
        )
        .values(status="UTILIZADA", consumido_em=now_utc(), versao=AutorizacaoSenha.versao + 1)
    )
    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(403, "Solicite ao administrador a autorização para trocar sua senha")


def revogar(session, usuario_id):
    session.exec(
        update(AutorizacaoSenha)
        .where(
            AutorizacaoSenha.usuario_id == usuario_id,
            AutorizacaoSenha.status.in_(["PENDENTE", "AUTORIZADA"]),
        )
        .values(status="REVOGADA", expira_em=None, versao=AutorizacaoSenha.versao + 1)
    )
