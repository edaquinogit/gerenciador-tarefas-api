import streamlit as st
import requests
import time
import random
import os  
from dotenv import load_dotenv 

load_dotenv()

# Configuração da URL da API
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

class TaskService:
    @staticmethod
    def login(username, password):
        try:
            response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
            return response.json() if response.status_code == 200 else None
        except: return None

    @staticmethod
    def listar(token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(f"{API_URL}/tarefas", headers=headers)
            return response.json() if response.status_code == 200 else []
        except: return []

    @staticmethod
    def concluir(tarefa_id, token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            res = requests.patch(f"{API_URL}/tarefas/{tarefa_id}/concluir", headers=headers)
            return res.status_code == 200
        except: return False

    @staticmethod
    def deletar(tarefa_id, token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return requests.delete(f"{API_URL}/tarefas/{tarefa_id}", headers=headers).status_code == 200
        except: return False

st.set_page_config(page_title="Pro Task Manager", layout="centered", page_icon="🎯")

# --- AUTH LOGIC ---
if "access_token" not in st.session_state:
    st.title("🎯 Task Manager")
    tab1, tab2 = st.tabs(["🔑 Acessar", "📝 Criar Conta"])
    with tab1:
        with st.form("login"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Sistema"):
                res = TaskService.login(user, pw)
                if res:
                    st.session_state["access_token"] = res["access_token"]
                    st.session_state["username"] = user
                    st.rerun()
                else: st.error("Credenciais inválidas.")

    with tab2:
        if "n1" not in st.session_state:
            st.session_state.n1, st.session_state.n2 = random.randint(1,9), random.randint(1,9)
        with st.form("register"):
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_pw = st.text_input("Password", type="password")
            st.write(f"🔢 Verificação: Quanto é {st.session_state.n1} + {st.session_state.n2}?")
            captcha = st.number_input("Resposta", min_value=0, step=1)
            if st.form_submit_button("Finalizar Cadastro"):
                if captcha == (st.session_state.n1 + st.session_state.n2):
                    payload = {"username": new_user, "email": new_email, "password": new_pw}
                    res = requests.post(f"{API_URL}/usuarios", json=payload)
                    if res.status_code == 201:
                        st.success("Conta criada! Faça login.")
                        del st.session_state.n1 
                    else: st.error("Erro no cadastro.")

# --- DASHBOARD LOGADO ---
else:
    token = st.session_state["access_token"]
    
    with st.sidebar:
        st.header(f"👤 {st.session_state.get('username', 'Perfil')}")
        if st.button("🚪 Encerrar Sessão"):
            st.session_state.clear()
            st.rerun()

    # BUSCAR TAREFAS UMA ÚNICA VEZ
    tarefas = TaskService.listar(token)
    if tarefas is None: tarefas = []

    st.title("📝 Minhas Tarefas")

    # PROGRESSO
    if tarefas:
        total = len(tarefas)
        num_concluidas = len([t for t in tarefas if t.get("concluido")])
        percentual = num_concluidas / total if total > 0 else 0.0
        
        st.write(f"**Progresso: {int(percentual * 100)}%** ({num_concluidas}/{total})")
        st.progress(percentual)
        if percentual == 1.0 and total > 0:
            st.balloons()
            st.success("🏆 Tudo pronto por hoje!")

    # NOVA TAREFA
    with st.expander("➕ Adicionar Nova Tarefa"):
        with st.form("new_task", clear_on_submit=True):
            titulo = st.text_input("Título da tarefa")
            prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta"], value="Média")
            if st.form_submit_button("Salvar Tarefa"):
                if titulo:
                    headers = {"Authorization": f"Bearer {token}"}
                    requests.post(f"{API_URL}/tarefas", json={"titulo": titulo, "prioridade": prioridade}, headers=headers)
                    st.rerun()

    st.divider()

    # LISTAGEM ÚNICA (Corrigida e Interativa)
    if not tarefas:
        st.info("Nenhuma tarefa para exibir.")
    else:
        for t in tarefas:
            is_done = t.get("concluido", False)
            t_id = t.get("id")
            t_titulo = t.get("titulo", "Sem título")
            
            with st.container():
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                
                with c1:
                    if is_done:
                        st.markdown(f"✅ ~~{t_titulo}~~")
                    else:
                        st.markdown(f"⏳ **{t_titulo}**")
                    st.caption(f"Prioridade: {t.get('prioridade', 'Média')}")
                
                with c2:
                    if not is_done:
                        if st.button("✔", key=f"done_{t_id}"):
                            with st.spinner("Concluindo..."):
                                if TaskService.concluir(t_id, token):
                                    st.toast(f"Feito: {t_titulo}")
                                    time.sleep(0.5)
                                    st.rerun()
                    else:
                        st.write("⭐")

                with c3:
                    if st.button("🗑️", key=f"del_{t_id}"):
                        if TaskService.deletar(t_id, token):
                            st.rerun()
                st.divider()