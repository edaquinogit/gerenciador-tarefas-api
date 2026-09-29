import os

import streamlit as st
from dotenv import load_dotenv

from frontend.services.task_service import APIError, TaskService

load_dotenv()
service = TaskService(os.getenv("API_URL", "http://127.0.0.1:8000"))
st.set_page_config(page_title="Gerenciador de Tarefas", page_icon="📋", layout="centered")


def report_error(error: APIError):
    if error.status_code == 401 and st.session_state.get("access_token"):
        st.session_state.clear()
        st.session_state["flash"] = "Sua sessão expirou. Entre novamente."
        st.rerun()
    st.error(str(error))


if message := st.session_state.pop("flash", None):
    st.info(message)

if not st.session_state.get("access_token"):
    st.title("Gerenciador de Tarefas")
    with st.form("login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            try:
                result = service.login(username, password)
                st.session_state.access_token = result["access_token"]
                st.session_state.username = username
                st.rerun()
            except APIError as error:
                report_error(error)
    st.caption("Para criar uma conta, solicite acesso ao responsável pelo sistema.")
    st.stop()

with st.sidebar:
    st.write(f"Usuário: {st.session_state.username}")
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()

token = st.session_state.access_token
st.title("Minhas tarefas")
try:
    tarefas = service.listar(token)
except APIError as error:
    report_error(error)
    if st.button("Tentar novamente"):
        st.rerun()
    st.stop()

with st.expander("Nova tarefa"):
    with st.form("nova_tarefa"):
        titulo = st.text_input("Título", max_chars=200)
        prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1)
        if st.form_submit_button("Adicionar"):
            if not titulo.strip():
                st.error("Informe o título da tarefa.")
            else:
                try:
                    service.criar(titulo.strip(), prioridade, token)
                    st.session_state.flash = "Tarefa criada."
                    st.rerun()
                except APIError as error:
                    report_error(error)

if not tarefas:
    st.info("Nenhuma tarefa cadastrada.")
else:
    concluidas = sum(t["concluido"] for t in tarefas)
    st.progress(concluidas / len(tarefas))
    st.caption(f"{concluidas} de {len(tarefas)} tarefas concluídas")
    for tarefa in tarefas:
        with st.container(border=True):
            st.text(tarefa["titulo"])
            st.caption(
                f"{tarefa['prioridade']} • {'Concluída' if tarefa['concluido'] else 'Pendente'}"
            )
            if not tarefa["concluido"] and st.button("Concluir", key=f"done_{tarefa['id']}"):
                try:
                    service.concluir(tarefa["id"], token)
                    st.session_state.flash = "Tarefa concluída."
                    st.rerun()
                except APIError as error:
                    report_error(error)
            with st.expander("Excluir tarefa"):
                st.caption("Esta exclusão é permanente.")
                if st.button("Confirmar exclusão", key=f"delete_{tarefa['id']}"):
                    try:
                        service.deletar(tarefa["id"], token)
                        st.session_state.flash = "Tarefa excluída."
                        st.rerun()
                    except APIError as error:
                        report_error(error)
