import os

import streamlit as st
from dotenv import load_dotenv

from frontend.services.task_service import APIError, TaskService
from frontend.views.admin import render_admin
from frontend.views.avisos import render_avisos
from frontend.views.conta import render_conta
from frontend.views.ordens import render_ordens
from frontend.views.painel import render_painel

load_dotenv()
service = TaskService(os.getenv("API_URL", "http://127.0.0.1:8000"))
st.set_page_config(page_title="Gerenciador de Tarefas", page_icon="📋", layout="centered")


if os.getenv("PILOT_MODE") == "true":
    st.warning("AMBIENTE DE TESTE — use somente dados fictícios.")


def clear_session():
    st.session_state.clear()


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

token = st.session_state.access_token
try:
    user = service.me(token)
except APIError as error:
    report_error(error)
    if st.button("Tentar novamente"):
        st.rerun()
    st.stop()

if user["perfil"] == "ADMIN":
    if st.button("Todas as tarefas", key="abrir_painel", type="primary"):
        st.session_state["pagina_principal"] = "Todas as tarefas"

with st.sidebar:
    st.write(f"Usuário: {user['username']}")
    st.caption("Administrador" if user["perfil"] == "ADMIN" else "Funcionário")
    nomes = {
        "SOLICITACAO": "Solicitação",
        "PRODUCAO": "Produção",
        "COLETA_EMBALAGEM": "Coleta e embalagem",
    }
    if user["perfil"] == "FUNCIONARIO":
        st.caption(f"Setor: {nomes.get(user['setor'], 'Aguardando definição')}")
    options = ["Minhas tarefas", "Minha conta"]
    if user["perfil"] == "ADMIN" or user["setor"] in nomes:
        options.insert(0, "Ordens de produção")
    if user["perfil"] == "ADMIN":
        options.insert(0, "Funcionários e setores")
        options.append("Todas as tarefas")
    if st.session_state.get("pagina_principal") not in options:
        st.session_state["pagina_principal"] = options[0]
    page = st.radio("Menu", options, key="pagina_principal")
    st.button("Sair", on_click=clear_session)

if user["perfil"] == "ADMIN" or user["setor"] in nomes:
    render_avisos(service, token, report_error)

if page == "Todas as tarefas" and user["perfil"] == "ADMIN":
    render_painel(service, token, report_error)
    st.stop()

if page == "Ordens de produção":
    render_ordens(service, token, user, report_error)
    st.stop()
if page == "Funcionários e setores":
    render_admin(service, token, report_error)
    st.stop()
if page == "Minha conta":
    render_conta(service, token, user, report_error)
    st.stop()
if user["perfil"] == "FUNCIONARIO" and not user["setor"]:
    st.warning("Seu setor ainda não foi definido. Solicite a classificação ao administrador.")

st.title("Minhas tarefas")
st.caption("O administrador também pode acompanhar estas tarefas no painel geral.")
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
