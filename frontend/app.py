import streamlit as st
import requests
import time
import random
import os
from dotenv import load_dotenv

# =====================
# CONFIG
# =====================
load_dotenv()
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Pro Task Manager",
    layout="centered",
    page_icon="🎯",
)

# Estilo CSS para animações e setas
st.markdown("""
    <style>
    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        10% { transform: translate(-1px, -2px) rotate(-1deg); }
        30% { transform: translate(3px, 2px) rotate(0deg); }
        50% { transform: translate(-1px, 2px) rotate(1deg); }
        70% { transform: translate(3px, 1px) rotate(-1deg); }
        100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
    .shake { display: inline-block; animation: shake 0.5s; }
    .done-arrow { color: #2ecc71; font-weight: bold; margin-right: 10px; }
    </style>
""", unsafe_allow_html=True)

# =====================
# SERVICE LAYER
# =====================
class TaskService:
    @staticmethod
    def login(username, password):
        try:
            res = requests.post(f"{API_URL}/token", data={"username": username, "password": password}, timeout=10)
            return res.json() if res.status_code == 200 else None
        except: return None

    @staticmethod
    def listar(token):
        try:
            res = requests.get(f"{API_URL}/tarefas", headers={"Authorization": f"Bearer {token}"}, timeout=10)
            return res.json() if res.status_code == 200 else []
        except: return []

    @staticmethod
    def criar(titulo, prioridade, token):
        try:
            payload = {"titulo": titulo, "descricao": "", "prioridade": prioridade, "concluida": False}
            res = requests.post(f"{API_URL}/tarefas", json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            return res.status_code in (200, 201)
        except: return False

    @staticmethod
    def concluir(tarefa_id, token):
        try:
            res = requests.patch(f"{API_URL}/tarefas/{tarefa_id}/concluir", headers={"Authorization": f"Bearer {token}"}, timeout=10)
            return res.status_code == 200
        except: return False

    @staticmethod
    def deletar(tarefa_id, token):
        try:
            res = requests.delete(f"{API_URL}/tarefas/{tarefa_id}", headers={"Authorization": f"Bearer {token}"}, timeout=10)
            return res.status_code == 200
        except: return False

# =====================
# LÓGICA DE SESSÃO
# =====================
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None

# =====================
# TELA DE AUTH
# =====================
if st.session_state.access_token is None:
    st.title("🎯 Task Manager")
    tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

    with tab_login:
        with st.form("login"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                res = TaskService.login(username, password)
                if res:
                    st.session_state.access_token = res["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

    with tab_register:
        if "captcha" not in st.session_state:
            st.session_state.captcha = (random.randint(1, 9), random.randint(1, 9))
        n1, n2 = st.session_state.captcha
        with st.form("register"):
            new_user = st.text_input("Novo Usuário")
            email = st.text_input("Email")
            new_pwd = st.text_input("Senha", type="password")
            st.write(f"Quanto é {n1} + {n2}?")
            ans = st.number_input("Resposta", step=1)
            if st.form_submit_button("Criar Conta"):
                if ans == n1 + n2:
                    res = requests.post(f"{API_URL}/usuarios", json={"username": new_user, "email": email, "password": new_pwd})
                    if res.status_code == 201:
                        st.success("Conta criada!")
                        st.session_state.captcha = (random.randint(1, 9), random.randint(1, 9))
                else: st.error("Erro no cálculo.")

# =====================
# DASHBOARD (LOGADO)
# =====================
else:
    token = st.session_state.access_token
    tarefas = TaskService.listar(token)

    # Inicializa a variável de controle no estado da sessão
    if 'ultima_acao' not in st.session_state:
        st.session_state['ultima_acao'] = None

    with st.sidebar:
        st.header(f"👤 {st.session_state.username}")
        if st.sidebar.button("🚪 Sair"):
            st.session_state.clear()
            st.rerun()

    st.title("📝 Minhas Tarefas")

    # 1. BARRA DE PROGRESSO E LÓGICA DE CELEBRAÇÃO
    if tarefas:
        total = len(tarefas)
        concluidas = sum(1 for t in tarefas if t.get("concluida") or t.get("concluido"))
        
        progresso = concluidas / total
        st.progress(progresso)
        st.caption(f"🚀 {concluidas} de {total} tarefas concluídas ({int(progresso*100)}%)")

        # CELEBRAÇÃO 100%: Balões apenas quando termina TUDO
        if concluidas == total and total > 0:
            if st.session_state.get('ultima_acao') == 'concluir':
                st.balloons()
                st.success("🎯 Sensacional! Você limpou sua lista de tarefas!")
                st.session_state['ultima_acao'] = None 

    # 2. ADICIONAR NOVA TAREFA
    with st.expander("➕ Nova Tarefa"):
        with st.form("nova_tarefa", clear_on_submit=True):
            titulo = st.text_input("Título")
            prioridade = st.select_slider("Prioridade", ["Baixa", "Média", "Alta"], value="Média")
            if st.form_submit_button("Adicionar"):
                if titulo and TaskService.criar(titulo, prioridade, token):
                    st.session_state['ultima_acao'] = 'adicionar'
                    st.toast("Tarefa criada! ✨")
                    time.sleep(0.5)
                    st.rerun()

    st.divider()

    # 3. LISTAGEM DE TAREFAS
    if not tarefas:
        st.info("Sua lista está limpa! Descanse um pouco.")
    else:
        for t in tarefas:
            is_done = t.get("concluida") or t.get("concluido")
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
                
                with c1:
                    if is_done:
                        st.markdown(f"<span class='done-arrow'>✔</span> ~~{t['titulo']}~~", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{t['titulo']}**")
                    
                    prio = t.get('prioridade', 'Média')
                    if prio == "Alta": st.caption("🔴 Prioridade Alta")
                    elif prio == "Média": st.caption("🟡 Prioridade Média")
                    else: st.caption("🟢 Prioridade Baixa")

                with c2:
                    if not is_done:
                        if st.button("✔", key=f"done_{t['id']}"):
                            if TaskService.concluir(t["id"], token):
                                st.session_state['ultima_acao'] = 'concluir'
                                # Feedback visual com confetes no canto da tela
                                st.toast("🎊 Parabéns!") 
                                time.sleep(0.8) 
                                st.rerun()

                with c3:
                    if st.button("🗑️", key=f"del_{t['id']}"):
                        if TaskService.deletar(t["id"], token):
                            st.session_state['ultima_acao'] = 'deletar'
                            time.sleep(0.3)
                            st.rerun()