from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update

from backend.models import Usuario
from backend.models.ordem import EventoOrdem, Ordem, now_utc
from backend.schemas.ordem import ComandoOrdem, OrdemCreate
from backend.services.classificador_produtos import classificar_produto
from backend.services.notificacoes import gerar_produto_pronto

SETORES = {"SOLICITACAO", "PRODUCAO", "COLETA_EMBALAGEM"}
PROXIMA = {"PENDENTE": "CORTANDO", "CORTANDO": "COSTURANDO", "COSTURANDO": "PRONTO"}


def permitir(user: Usuario, setor: str | None = None):
    if user.perfil == "ADMIN":
        return
    if user.setor not in SETORES or (setor and user.setor != setor):
        raise HTTPException(403, "Seu setor não tem permissão para esta operação")


def buscar(session: Session, ident: int) -> Ordem:
    ordem = session.get(Ordem, ident)
    if ordem is None:
        raise HTTPException(404, "Ordem não encontrada")
    return ordem


def criar(session: Session, data: OrdemCreate, user: Usuario) -> Ordem:
    permitir(user, "SOLICITACAO")
    values = data.model_dump(exclude={"request_id"})
    request_id = str(data.request_id)
    categoria = classificar_produto(data.produto, data.especificacao, data.observacao)

    def existente():
        ordem = session.exec(select(Ordem).where(Ordem.request_id == request_id)).first()
        if ordem and (
            ordem.solicitante_id != user.id
            or any(getattr(ordem, key) != val for key, val in values.items())
        ):
            raise HTTPException(409, "Identificador de envio já utilizado com outros dados")
        return ordem

    if ordem := existente():
        return ordem
    ordem = Ordem(**values, request_id=request_id, solicitante_id=user.id, categoria=categoria)
    try:
        session.add(ordem)
        session.flush()
        session.add(
            EventoOrdem(
                request_id=request_id,
                ordem_id=ordem.id,
                usuario_id=user.id,
                usuario_nome=user.username,
                acao="CRIACAO",
                status_novo="PENDENTE",
                versao=1,
            )
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        if ordem := existente():
            return ordem
        raise HTTPException(409, "Conflito no envio. Atualize a fila e confira a ordem.") from None
    session.refresh(ordem)
    return ordem


def consulta_filtrada(status, situacao, categoria=None):
    query = select(Ordem)
    if categoria:
        query = query.where(Ordem.categoria == categoria)
    if status:
        query = query.where(Ordem.status == status)
    if situacao == "ativas":
        query = query.where(Ordem.cancelado_em.is_(None), Ordem.coletado_em.is_(None))
    elif situacao == "coletadas":
        query = query.where(Ordem.coletado_em.is_not(None))
    elif situacao == "canceladas":
        query = query.where(Ordem.cancelado_em.is_not(None))
    return query


def listar(session, user, status, situacao, offset, limit, categoria=None):
    permitir(user)
    query = consulta_filtrada(status, situacao, categoria)
    query = (
        query.order_by((Ordem.prioridade == "URGENTE").desc(), Ordem.prazo, Ordem.id)
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(query).all())


def contar(session, user, status, situacao, categoria=None):
    permitir(user)
    query = consulta_filtrada(status, situacao, categoria)
    return session.exec(select(func.count()).select_from(query.subquery())).one()


def executar(
    session: Session,
    ident: int,
    data: ComandoOrdem,
    user: Usuario,
    acao: str,
    destino: str | None = None,
    motivo: str = "",
) -> Ordem:
    if acao == "ETAPA":
        permitir(user, "PRODUCAO")
    elif acao == "COLETA":
        permitir(user, "COLETA_EMBALAGEM")
    elif acao == "CANCELAMENTO":
        if user.perfil != "ADMIN":
            raise HTTPException(403, "Somente o administrador pode cancelar ordens")
    request_id = str(data.request_id)

    def repetido():
        evento = session.exec(
            select(EventoOrdem).where(EventoOrdem.request_id == request_id)
        ).first()
        if not evento:
            return None
        if (
            evento.ordem_id != ident
            or evento.usuario_id != user.id
            or evento.acao != acao
            or evento.versao != data.versao + 1
            or evento.motivo != motivo
            or (destino and evento.status_novo != destino)
        ):
            raise HTTPException(409, "Identificador de envio já utilizado em outra operação")
        return buscar(session, ident)

    if ordem := repetido():
        return ordem
    ordem = buscar(session, ident)
    if ordem.versao != data.versao:
        raise HTTPException(
            409, "Ordem alterada por outra pessoa. Atualize a lista e tente novamente."
        )
    if ordem.cancelado_em or ordem.coletado_em:
        raise HTTPException(409, "Ordem já encerrada")
    now = now_utc()
    changes = {"versao": data.versao + 1, "atualizado_em": now}
    if acao == "ETAPA":
        if PROXIMA.get(ordem.status) != destino:
            raise HTTPException(
                409, "Etapa inválida. Siga pendente, cortando, costurando e pronto."
            )
        changes.update(status=destino, responsavel_id=user.id)
        if destino == "PRONTO":
            changes["pronto_em"] = now
    elif acao == "COLETA":
        if ordem.status != "PRONTO":
            raise HTTPException(409, "Somente ordens prontas podem ser coletadas")
        changes.update(coletado_em=now, coletado_por=user.id)
    elif acao == "CANCELAMENTO":
        changes["cancelado_em"] = now
    else:
        raise ValueError("Ação desconhecida")
    anterior = ordem.status
    try:
        result = session.exec(
            update(Ordem).where(Ordem.id == ident, Ordem.versao == data.versao).values(**changes)
        )
        if result.rowcount != 1:
            session.rollback()
            if repetida := repetido():
                return repetida
            raise HTTPException(409, "Ordem alterada por outra pessoa. Atualize a lista.")
        evento = EventoOrdem(
            request_id=request_id,
            ordem_id=ident,
            usuario_id=user.id,
            usuario_nome=user.username,
            acao=acao,
            status_anterior=anterior,
            status_novo=destino or anterior,
            motivo=motivo,
            versao=data.versao + 1,
        )
        session.add(evento)
        if acao == "ETAPA" and destino == "PRONTO":
            gerar_produto_pronto(session, ordem, evento)
        session.commit()
    except IntegrityError:
        session.rollback()
        if repetida := repetido():
            return repetida
        raise HTTPException(409, "Conflito no envio. Atualize a fila e confira a ordem.") from None
    session.refresh(ordem)
    return ordem


def apresentar(session: Session, ordem: Ordem) -> dict:
    result = ordem.model_dump()
    result["solicitante_nome"] = session.get(Usuario, ordem.solicitante_id).username
    result["responsavel_nome"] = (
        session.get(Usuario, ordem.responsavel_id).username if ordem.responsavel_id else None
    )
    result["coletado_nome"] = (
        session.get(Usuario, ordem.coletado_por).username if ordem.coletado_por else None
    )
    return result
