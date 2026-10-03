from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.core.security import get_current_user, require_admin
from backend.database.connection import get_session
from backend.models import Usuario
from backend.schemas.usuario import (
    DecisaoSenha,
    FuncionarioCreate,
    FuncionarioUpdate,
    MeuTelefoneUpdate,
    MinhaSenhaUpdate,
    SenhaUpdate,
    UsuarioRead,
)
from backend.services import autorizacoes_senha, usuarios

router = APIRouter(tags=["Funcionários e setores"])
SETORES = [
    {"id": "SOLICITACAO", "nome": "Solicitação"},
    {"id": "PRODUCAO", "nome": "Produção"},
    {"id": "COLETA_EMBALAGEM", "nome": "Coleta e embalagem"},
]


@router.get("/usuarios/me/autorizacao-senha")
def minha_autorizacao(
    session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)
):
    return autorizacoes_senha.consultar(session, user)


@router.post("/usuarios/me/autorizacao-senha")
def solicitar_senha(
    session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)
):
    return autorizacoes_senha.solicitar(session, user)


@router.get("/admin/autorizacoes-senha")
def autorizacoes(session: Session = Depends(get_session), admin: Usuario = Depends(require_admin)):
    return autorizacoes_senha.listar(session)


@router.post("/admin/funcionarios/{usuario_id}/autorizacao-senha")
def decidir_senha(
    usuario_id: int,
    data: DecisaoSenha,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(require_admin),
):
    return autorizacoes_senha.decidir(session, usuario_id, admin, data.permitir, data.versao)


@router.get("/setores")
def setores(user: Usuario = Depends(get_current_user)):
    return SETORES


@router.get("/admin/funcionarios", response_model=list[UsuarioRead])
def listar(session: Session = Depends(get_session), admin: Usuario = Depends(require_admin)):
    return usuarios.listar_funcionarios(session)


@router.post("/admin/funcionarios", response_model=UsuarioRead, status_code=201)
def criar(
    data: FuncionarioCreate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(require_admin),
):
    return usuarios.criar_usuario(session, data, setor=data.setor)


@router.patch("/admin/funcionarios/{usuario_id}", response_model=UsuarioRead)
def atualizar(
    usuario_id: int,
    data: FuncionarioUpdate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(require_admin),
):
    return usuarios.atualizar_funcionario(session, usuario_id, data)


@router.post("/admin/funcionarios/{usuario_id}/senha")
def redefinir_senha(
    usuario_id: int,
    data: SenhaUpdate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(require_admin),
):
    user = usuarios.buscar_funcionario(session, usuario_id)
    usuarios.redefinir_senha(session, user, data.password)
    return {"message": "Senha redefinida. O funcionário precisa entrar novamente."}


@router.post("/usuarios/me/senha")
def minha_senha(
    data: MinhaSenhaUpdate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    usuarios.alterar_minha_senha(session, user, data.current_password, data.password)
    return {"message": "Senha alterada. Entre novamente."}


@router.patch("/usuarios/me/telefone", response_model=UsuarioRead)
def meu_telefone(
    data: MeuTelefoneUpdate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return usuarios.atualizar_meu_telefone(session, user, data.telefone)
