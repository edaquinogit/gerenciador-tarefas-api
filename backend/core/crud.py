from sqlmodel import Session, select
from fastapi import HTTPException, status

from database.models import Usuario, UsuarioCreate, Tarefa, TarefaCreate

# =====================================================
# USUÁRIOS
# =====================================================

def criar_usuario(
    session: Session,
    usuario_data: UsuarioCreate,
    senha_hash: str
) -> Usuario:
    """
    Cria um novo usuário no sistema.
    A senha já deve vir hasheada.
    """

    # Verifica se username já existe
    usuario_existente = session.exec(
        select(Usuario).where(Usuario.username == usuario_data.username)
    ).first()

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já existe"
        )

    novo_usuario = Usuario(
        username=usuario_data.username,
        email=usuario_data.email,
        password_hash=senha_hash,
        is_active=True,
        is_admin=False
    )

    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)

    return novo_usuario


def listar_usuarios(session: Session) -> list[Usuario]:
    return session.exec(select(Usuario)).all()


def buscar_usuario_por_id(
    session: Session,
    usuario_id: int
) -> Usuario | None:
    return session.get(Usuario, usuario_id)


def deletar_usuario(
    session: Session,
    usuario_id: int
) -> None:
    usuario = session.get(Usuario, usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    session.delete(usuario)
    session.commit()


# =====================================================
# TAREFAS
# =====================================================

def criar_tarefa(
    session: Session,
    tarefa_data: TarefaCreate,
    usuario_id: int
) -> Tarefa:
    """
    Cria uma tarefa vinculada ao usuário autenticado.
    """

    tarefa = Tarefa(
        titulo=tarefa_data.titulo,
        prioridade=tarefa_data.prioridade,
        usuario_id=usuario_id
    )

    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)

    return tarefa


def listar_tarefas_usuario(
    session: Session,
    usuario_id: int
) -> list[Tarefa]:
    return session.exec(
        select(Tarefa).where(Tarefa.usuario_id == usuario_id)
    ).all()


def buscar_tarefa_por_id(
    session: Session,
    tarefa_id: int
) -> Tarefa | None:
    return session.get(Tarefa, tarefa_id)


def concluir_tarefa(
    session: Session,
    tarefa_id: int,
    usuario_id: int
) -> Tarefa:
    tarefa = session.get(Tarefa, tarefa_id)

    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada"
        )

    if tarefa.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    tarefa.concluido = True
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)

    return tarefa


def deletar_tarefa(
    session: Session,
    tarefa_id: int,
    usuario_id: int
) -> None:
    tarefa = session.get(Tarefa, tarefa_id)

    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada"
        )

    if tarefa.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    session.delete(tarefa)
    session.commit()
