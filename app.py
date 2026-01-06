import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# --- FUNÇÕES DE APOIO ---
def login_api(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{API_URL}/token", data=payload)
    return response.json() if response.status_code == 200 else None

def listar_tarefas_api(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/tarefas", headers=headers)
    return response.json() if response.status_code == 200 else []

# --- INTERFACE ---
st.set_page_config(page_title="Task Manager", layout="wide")
st.title("Gerenciador de Tarefas 🚀")

if "access_token" not in st.session_state:
    # TELA DE LOGIN
    with st.form("login_form"):
        st.subheader("Login")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            res = login_api(user, pw)
            if res:
                st.session_state["access_token"] = res["access_token"]
                st.rerun()
            else:
                st.error("Falha no login")
else:
    # DASHBOARD
    with st.sidebar:
        if st.button("Sair"):
            del st.session_state["access_token"]
            st.rerun()

    # Formulário de Nova Tarefa
    with st.expander("➕ Nova Tarefa"):
        with st.form("add_task"):
            titulo = st.text_input("Título")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"])
            if st.form_submit_button("Criar"):
                headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
                requests.post(f"{API_URL}/tarefas", json={"titulo": titulo, "prioridade": prioridade}, headers=headers)
                st.rerun()

    # Listagem de Tarefas
    st.subheader("Suas Atividades")
    tarefas = listar_tarefas_api(st.session_state["access_token"])
    for t in tarefas:
        with st.container(border=True):
            st.write(f"**{t['titulo']}**")
            st.caption(f"Prioridade: {t['prioridade']}")