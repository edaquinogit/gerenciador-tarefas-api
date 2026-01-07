import streamlit as st
import requests
import time
import random

# Configuração de ambiente
API_URL = "http://127.0.0.1:8000"

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

# Custom CSS para melhorar a estética
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .task-card { padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Task Manager")
st.caption("Organização inteligente para desenvolvedores de alto nível!")
st.caption("Desenvolvedor: Ednaldo Aquino.")

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
                        del st.session_state.n1 # Reseta o captcha
                    else: st.error("Erro: Usuário já cadastrado.")
                else: st.error("Soma incorreta!")

# --- DASHBOARD LOGADO ---
else:
    token = st.session_state["access_token"]
    
    with st.sidebar:
        st.header("👤 Perfil")
        st.info("Logado com sucesso")
        if st.button("🚪 Encerrar Sessão"):
            del st.session_state["access_token"]
            st.rerun()

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
                    time.sleep(1)
                    st.rerun()

    # Listagem Profissional
    st.divider()
    tarefas = TaskService.listar(token)
    
    if not tarefas:
        st.write("✨ *Você não tem tarefas pendentes. Aproveite o descanso!*")
    else:
        for t in tarefas:
            # Pegamos os dados com segurança usando .get()
            is_done = t.get("concluido", False)
            t_id = t.get("id")
            t_titulo = t.get("titulo", "Sem título")
            
            with st.container():
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                
                with col1:
                    if is_done:
                        st.markdown(f"✅ ~~{t_titulo}~~")
                    else:
                        st.markdown(f"⏳ **{t_titulo}**")
                    st.caption(f"Prioridade: {t.get('prioridade', 'Média')}")
                
                with col2:
                    # O botão de concluir só aparece se a tarefa não estiver pronta
                    if not is_done:
                        if st.button("✔", key=f"done_{t_id}"):
                            if TaskService.concluir(t_id, token):
                                st.balloons()
                                st.success("🎊 EXCELENTE TRABALHO!")
                                time.sleep(13)
                                st.rerun()
                    else:
                        st.markdown("⭐")
                
                with col3:
                    # LINHA CORRIGIDA: A lixeira agora tem uma chave única fechada corretamente
                    if st.button("🗑️", key=f"del_{t_id}"):
                        if TaskService.deletar(t_id, token):
                            st.toast("Tarefa removida.")
                            time.sleep(1)
                            st.rerun()
                st.divider()