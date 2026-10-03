from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update

from backend.core.security import get_password_hash, verify_password
from backend.models import Usuario
from backend.schemas.usuario import FuncionarioUpdate, UsuarioCreate
from backend.services import autorizacoes_senha


def criar_usuario(
    session: Session, data: UsuarioCreate, *, perfil: str = "FUNCIONARIO", setor: str | None = None
) -> Usuario:
    user = Usuario(
        username=data.username,
        telefone=data.telefone,
        password_hash=get_password_hash(data.password),
        perfil=perfil,
        setor=setor,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Nome de usuário já cadastrado") from None
    session.refresh(user)
    return user


def listar_funcionarios(session: Session) -> list[Usuario]:
    return list(
        session.exec(
            select(Usuario).where(Usuario.perfil == "FUNCIONARIO").order_by(Usuario.username)
        ).all()
    )


def buscar_funcionario(session: Session, usuario_id: int) -> Usuario:
    user = session.get(Usuario, usuario_id)
    if not user:
        raise HTTPException(404, "Funcionário não encontrado")
    if user.perfil != "FUNCIONARIO":
        raise HTTPException(403, "A conta administrativa não pode ser alterada neste painel")
    return user


def atualizar_funcionario(session: Session, usuario_id: int, data: FuncionarioUpdate) -> Usuario:
    buscar_funcionario(session, usuario_id)
    autorizacoes_senha.revogar(session, usuario_id)
    contato = {"telefone": data.telefone} if "telefone" in data.model_fields_set else {}
    session.exec(
        update(Usuario)
        .where(Usuario.id == usuario_id)
        .values(
            **contato,
            setor=data.setor,
            is_active=data.is_active,
            token_version=Usuario.token_version + 1,
        )
    )
    session.commit()
    session.expire_all()
    return session.get(Usuario, usuario_id)


def redefinir_senha(session: Session, user: Usuario, password: str) -> None:
    result = session.exec(
        update(Usuario)
        .where(Usuario.id == user.id, Usuario.token_version == user.token_version)
        .values(
            password_hash=get_password_hash(password),
            token_version=Usuario.token_version + 1,
        )
    )
    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "Conta alterada. Entre novamente e tente outra vez.")
    autorizacoes_senha.revogar(session, user.id)
    session.commit()


def alterar_minha_senha(
    session: Session, user: Usuario, current_password: str, password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(400, "Senha atual incorreta")
    autorizacoes_senha.consumir(session, user)
    redefinir_senha(session, user, password)


def criar_primeiro_admin(session: Session, data: UsuarioCreate) -> Usuario:
    # Comando local de manutenção: executar uma única instância, com a API parada.
    if session.exec(select(Usuario).where(Usuario.perfil == "ADMIN")).first():
        raise HTTPException(409, "Administrador já existe; bootstrap recusado")
    return criar_usuario(session, data, perfil="ADMIN")


def atualizar_meu_telefone(session: Session, user: Usuario, telefone: str) -> Usuario:
    session.exec(update(Usuario).where(Usuario.id == user.id).values(telefone=telefone))
    session.commit()
    session.refresh(user)
    return user
