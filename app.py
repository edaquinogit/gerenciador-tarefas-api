import streamlit as st
import requests
import time
import random
import os  
from dotenv import load_dotenv 

# 1. Carrega as configurações do arquivo .env
load_dotenv()

# 2. Busca a URL da API. Se não encontrar no .env, usa o localhost por padrão
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- SERVICE LAYER (Comunicação com a API) ---
class TaskService:
    @staticmethod
    def login(username, password):
        try:
            response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.ConnectionError:
            st.error("Erro: Backend offline! Certifique-se que o Uvicorn está rodando.")
            return None

    @staticmethod
    def listar(token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(f"{API_URL}/tarefas", headers=headers)
            if response.status_code == 401:
                st.session_state.clear()
                st.rerun()
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

# --- UI CONFIG ---
st.set_page_config(page_title="Pro Task Manager", layout="centered", page_icon="🎯")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Task Manager")
st.caption("Organização inteligente | Desenvolvedor: Ednaldo Aquino.")

# --- AUTH LOGIC ---
if "access_token" not in st.session_state:
    tab1, tab2 = st.tabs(["🔑 Acessar", "📝 Criar Conta"])
    with tab1:
        with st.form("login"):
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Sistema"):
                res = TaskService.login(user, pw)
                if res:
                    st.session_state["access_token"] = res["access_token"]
                    st.toast("Bem-vindo de volta!", icon="🚀")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Credenciais inválidas.")

    with tab2:
        if "n1" not in st.session_state:
            st.session_state.n1, st.session_state.n2 = random.randint(1,9), random.randint(1,9)
        with st.form("register"):
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_pw = st.text_input("Password", type="password")
            st.write(f"🔢 Verificação: Quanto é **{st.session_state.n1} + {st.session_state.n2}**?")
            captcha = st.number_input("Resposta", min_value=0, step=1)
            if st.form_submit_button("Finalizar Cadastro"):
                if captcha == (st.session_state.n1 + st.session_state.n2):
                    payload = {"username": new_user, "email": new_email, "password": new_pw}
                    res = requests.post(f"{API_URL}/usuarios", json=payload)
                    if res.status_code == 201:
                        st.success("Conta criada! Já pode fazer login.")
                        del st.session_state.n1 
                    else: st.error("Erro: Usuário já cadastrado.")
                else: st.error("Soma incorreta!")

# --- DASHBOARD LOGADO ---
else:
    token = st.session_state["access_token"]
    
    with st.sidebar:
        st.header("👤 Perfil")
        st.info("Logado com sucesso")
        if st.button("🚪 Encerrar Sessão"):
            st.session_state.clear()
            st.rerun()

    # --- REFINAMENTO: CÁLCULO DE PROGRESSO ---
    tarefas = TaskService.listar(token)
    
    if tarefas:
        total = len(tarefas)
        num_concluidas = len([t for t in tarefas if t.get("concluido")])
        percentual = num_concluidas / total if total > 0 else 0.0
        
        st.subheader("📊 Seu Desempenho")
        col_bar, col_txt = st.columns([4, 1])
        with col_bar:
            st.progress(percentual)
        with col_txt:
            st.write(f"**{int(percentual * 100)}%**")
        
        # Celebrações baseadas no progresso
        if percentual == 1.0 and total > 0:
            st.balloons()
            st.success("🏆 **Incrível! Você concluiu todas as tarefas de hoje!**")
        elif percentual >= 0.5:
            st.info("⚡ **Boa! Você já passou da metade!**")
    
    # Adicionar Tarefa
    with st.expander("➕ Nova Tarefa", expanded=False):
        with st.form("new_task", clear_on_submit=True):
            titulo = st.text_input("O que vamos realizar hoje?")
            prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta"])
            if st.form_submit_button("Agendar Tarefa"):
                if titulo:
                    headers = {"Authorization": f"Bearer {token}"}
                    requests.post(f"{API_URL}/tarefas", json={"titulo": titulo, "prioridade": prioridade}, headers=headers)
                    st.toast("Tarefa agendada!", icon="📅")
                    time.sleep(0.5)
                    st.rerun()

    st.divider()
    
    if not tarefas:
        st.write("✨ *Nenhuma tarefa por aqui. Que tal planejar seu dia?*")
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
                            if TaskService.concluir(t_id, token):
                                st.toast("Tarefa concluída!")
                                time.sleep(0.5)
                                st.rerun()
                    else:
                        st.markdown("⭐")
                
                with c3:
                    if st.button("🗑️", key=f"del_{t_id}"):
                        if TaskService.deletar(t_id, token):
                            st.toast("Tarefa removida.")
                            time.sleep(0.5)
                            st.rerun()
                st.divider()