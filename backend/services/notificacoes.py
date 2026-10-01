from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlmodel import Session, select, update

from backend.models.notificacao import Notificacao
from backend.models.ordem import EventoOrdem, Ordem, now_utc
from backend.models.usuario import Usuario


def gerar_produto_pronto(session: Session, ordem: Ordem, evento: EventoOrdem):
    """Participa da transação da ordem; nunca faz commit independente."""
    session.flush()
    destinatarios = session.exec(
        select(Usuario).where(
            Usuario.is_active.is_(True),
            or_(
                Usuario.id == ordem.solicitante_id,
                Usuario.perfil == "ADMIN",
                Usuario.setor == "COLETA_EMBALAGEM",
            ),
        )
    ).all()
    for user in destinatarios:
        session.add(
            Notificacao(
                evento_id=evento.id,
                ordem_id=ordem.id,
                usuario_id=user.id,
                mensagem=f"Ordem #{ordem.id} ficou pronta: {ordem.quantidade} {ordem.unidade} de {ordem.produto}.",
            )
        )


def situacao(ordem: Ordem) -> str:
    if ordem.cancelado_em:
        return "CANCELADA"
    if ordem.coletado_em:
        return "COLETADA"
    return "AGUARDANDO_COLETA" if ordem.status == "PRONTO" else "EM_PRODUCAO"


def listar(session: Session, user: Usuario, somente_nao_lidas: bool, offset: int, limit: int):
    total = session.exec(
        select(func.count())
        .select_from(Notificacao)
        .where(Notificacao.usuario_id == user.id, Notificacao.lida_em.is_(None))
    ).one()
    query = (
        select(Notificacao, Ordem)
        .join(Ordem, Ordem.id == Notificacao.ordem_id)
        .where(Notificacao.usuario_id == user.id)
    )
    if somente_nao_lidas:
        query = query.where(Notificacao.lida_em.is_(None))
    filtrado = session.exec(select(func.count()).select_from(query.subquery())).one()
    rows = session.exec(query.order_by(Notificacao.id.desc()).offset(offset).limit(limit)).all()
    return {
        "nao_lidas": total,
        "total": filtrado,
        "itens": [{**notice.model_dump(), "situacao": situacao(ordem)} for notice, ordem in rows],
    }


def marcar_lida(session: Session, ident: int, user: Usuario):
    result = session.exec(
        update(Notificacao)
        .where(Notificacao.id == ident, Notificacao.usuario_id == user.id)
        .values(lida_em=func.coalesce(Notificacao.lida_em, now_utc()))
    )
    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(404, "Aviso não encontrado")
    session.commit()
    return {"message": "Aviso marcado como lido. A coleta deve ser confirmada na ordem."}
