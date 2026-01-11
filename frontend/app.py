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

API_URL = (
    st.secrets.get("API_URL")
    if hasattr(st, "secrets")
    else None
) or os.getenv("API_URL") or "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Pro Task Manager",
    layout="centered",
    page_icon="🎯",
)

# =====================
# SERVICE LAYER
# =====================
class TaskService:
    @staticmethod
    def login(username, password):
        try:
            res = requests.post(
                f"{API_URL}/token",
                data={"username": username, "password": password},
                timeout=10,
            )
            return res.json() if res.status_code == 200 else None
        except:
            return None

    @staticmethod
    def listar(token):
        try:
            res = requests.get(
                f"{API_URL}/tarefas",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return res.json() if res.status_code == 200 else []
        except:
            return []

    @staticmethod
    def criar(titulo, prioridade, token):
        try:
            res = requests.post(
                f"{API_URL}/tarefas",
                json={"titulo": titulo, "prioridade": prioridade},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return res.status_code in (200, 201)
        except:
            return False

    @staticmethod
    def concluir(tarefa_id, token):
        try:
            res = requests.patch(
                f"{API_URL}/tarefas/{tarefa_id}/concluir",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return res.status_code == 200
        except:
            return False

    @staticmethod
    def deletar(tarefa_id, token):
        try:
            res = requests.delete(
                f"{API_URL}/tarefas/{tarefa_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return res.status_code == 200
        except:
            return False

# =====================
# AUTH
# =====================
if "access_token" not in st.session_state:
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
                    st.error("Usuário ou senha inválidos.")

    with tab_register:
        if "captcha" not in st.session_state:
            st.session_state.captcha = (
                random.randint(1, 9),
                random.randint(1, 9),
            )

        n1, n2 = st.session_state.captcha

        with st.form("register"):
            new_user = st.text_input("Usuário")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")

            st.write(f"🔢 Quanto é {n1} + {n2}?")
            answer = st.number_input("Resposta", step=1)

            if st.form_submit_button("Criar Conta"):
                if answer != n1 + n2:
                    st.error("Verificação incorreta.")
                else:
                    res = requests.post(
                        f"{API_URL}/usuarios",
                        json={
                            "username": new_user,
                            "email": email,
                            "password": password,
                        },
                    )
                    if res.status_code == 201:
                        st.success("Conta criada! Faça login.")
                        del st.session_state.captcha
                    else:
                        st.error("Erro ao criar conta.")

# =====================
# DASHBOARD
# =====================
else:
    token = st.session_state.access_token

    tarefas = TaskService.listar(token)

    with st.sidebar:
        st.header(f"👤 {st.session_state.username}")
        if st.button("🚪 Sair"):
            st.session_state.clear()
            st.rerun()

    st.title("📝 Minhas Tarefas")

    # PROGRESSO
    if tarefas:
        total = len(tarefas)
        concluidas = sum(1 for t in tarefas if t["concluido"])
        progresso = concluidas / total
        st.progress(progresso)
        st.caption(f"{concluidas}/{total} concluídas")

        if progresso == 1:
            st.balloons()
            st.success("🏆 Todas concluídas!")

    # NOVA TAREFA
    with st.expander("➕ Nova Tarefa"):
        with st.form("nova_tarefa", clear_on_submit=True):
            titulo = st.text_input("Título")
            prioridade = st.select_slider(
                "Prioridade", ["Baixa", "Média", "Alta"], value="Média"
            )

            if st.form_submit_button("Adicionar"):
                if titulo:
                    if TaskService.criar(titulo, prioridade, token):
                        st.toast("Tarefa criada!", icon="📌")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.warning("Digite um título.")

    st.divider()

    # LISTAGEM
    if not tarefas:
        st.info("Nenhuma tarefa cadastrada.")
    else:
        for t in tarefas:
            with st.container():
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])

                with c1:
                    if t["concluido"]:
                        st.markdown(
                            f"✅ <s>{t['titulo']}</s>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"⏳ **{t['titulo']}**")
                    st.caption(f"Prioridade: {t.get('prioridade', 'Média')}")

                with c2:
                    if not t["concluido"]:
                        if st.button("✔", key=f"done_{t['id']}"):
                            if TaskService.concluir(t["id"], token):
                                st.rerun()
                    else:
                        st.write("🌟")

                with c3:
                    if st.button("🗑️", key=f"del_{t['id']}"):
                        if TaskService.deletar(t["id"], token):
                            st.rerun()

                st.divider()
