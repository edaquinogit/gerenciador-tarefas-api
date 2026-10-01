import streamlit as st

from frontend.services.task_service import APIError
from frontend.session import reset_local
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
