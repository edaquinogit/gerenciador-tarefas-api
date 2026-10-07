import streamlit as st

from frontend.services.task_service import APIError
from frontend.session import reset_local
from frontend.views.ordens import horario
from shared.telefone import normalizar_telefone


def render_conta(service, token, user, report_error):
    st.title("Minha conta")
    st.text(f"Usuário: {user['username']}")
    st.text(f"Telefone: {user['telefone'] or 'Não informado'}")
    with st.form("meu_telefone"):
        telefone = st.text_input(
            "Telefone com DDD",
            value=user["telefone"] or "",
            max_chars=32,
            placeholder="(79) 99999-0000",
        )
        if st.form_submit_button("Salvar telefone"):
            try:
                service.meu_telefone(normalizar_telefone(telefone), token)
                st.session_state.flash = "Telefone atualizado."
                st.rerun()
            except ValueError as error:
                st.error(str(error))
            except APIError as error:
                report_error(error)
    render_senha(service, token, user, report_error)


@st.fragment(run_every="10s")
def render_senha(service, token, user, report_error):
    token = st.session_state.get("access_token", token)
    st.subheader("Alterar senha")
    if user["perfil"] != "ADMIN":
        try:
            autorizacao = service.autorizacao_senha(token)
        except APIError as error:
            report_error(error)
            return
        status = autorizacao["status"]
        if status != "AUTORIZADA":
            if status == "PENDENTE":
                st.info("Solicitação enviada. Aguardando autorização do administrador.")
            else:
                mensagens = {
                    "RECUSADA": "Solicitação recusada pelo administrador.",
                    "EXPIRADA": "A autorização expirou. Solicite uma nova liberação.",
                    "REVOGADA": "A autorização anterior foi revogada.",
                }
                st.caption(
                    mensagens.get(
                        status, "Para trocar sua senha, solicite autorização ao administrador."
                    )
                )
                if st.button("Solicitar alteração de senha"):
                    try:
                        service.solicitar_senha(token)
                        st.rerun()
                    except APIError as error:
                        report_error(error)
            return
        st.success(f"Uma troca autorizada até {horario(autorizacao['expira_em'])} (Bahia).")
    with st.form("minha_senha", clear_on_submit=True):
        current = st.text_input("Senha atual", type="password")
        password = st.text_input("Nova senha", type="password")
        confirm = st.text_input("Confirme a nova senha", type="password")
        if st.form_submit_button("Alterar minha senha"):
            if password != confirm or len(password) < 8 or len(password.encode()) > 72:
                st.error("Confirme uma senha com mínimo de 8 caracteres e máximo de 72 bytes.")
            else:
                try:
                    service.minha_senha(current, password, token)
                    reset_local("Senha alterada. Entre novamente.")
                    st.rerun()
                except APIError as error:
                    report_error(error)
