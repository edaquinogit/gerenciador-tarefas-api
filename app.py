import streamlit as st
import requests
import time
import random
import os  
from dotenv import load_dotenv 

load_dotenv()

# Configuração da URL da API
API_URL = st.secrets.get("API_URL") or os.getenv("API_URL") or "https://gerenciador-tarefas-api-des-ednaldo.onrender.com"
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
    
    # 1. BUSCA DE DADOS (Sempre no topo para garantir sincronia)
    tarefas = TaskService.listar(token)
    if tarefas is None: 
        tarefas = []

    # 2. BARRA LATERAL
    with st.sidebar:
        st.header(f"👤 {st.session_state.get('username', 'Usuário')}")
        if st.button("🚪 Encerrar Sessão"):
            st.session_state.clear()
            st.rerun()

    st.title("📝 Minhas Tarefas")

    # 3. CÁLCULO DE PROGRESSO E BALÕES
    if tarefas:
        total = len(tarefas)
        concluidas = [t for t in tarefas if t.get("concluido")]
        num_concluidas = len(concluidas)
        percentual = num_concluidas / total if total > 0 else 0.0
        
        st.write(f"**Progresso: {int(percentual * 100)}%** ({num_concluidas}/{total})")
        st.progress(percentual)
        
        # Só solta os balões se ACABOU de completar a última tarefa
        if percentual == 1.0 and total > 0:
            st.balloons()
            st.success("🏆 Sensacional! Você completou tudo!")

    # 4. ADICIONAR TAREFA
    with st.expander("➕ Nova Tarefa"):
        with st.form("new_task", clear_on_submit=True):
            titulo = st.text_input("Título")
            prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta"], value="Média")
            if st.form_submit_button("Agendar"):
                if titulo:
                    headers = {"Authorization": f"Bearer {token}"}
                    res = requests.post(f"{API_URL}/tarefas", json={"titulo": titulo, "prioridade": prioridade}, headers=headers)
                    if res.status_code in [200, 201]:
                        st.rerun()

    st.divider()

    # 5. LISTAGEM DE TAREFAS (Lógica de desaparecimento do botão)
    if not tarefas:
        st.info("Nenhuma tarefa pendente.")
    else:
        for t in tarefas:
            is_done = t.get("concluido", False)
            t_id = t.get("id")
            t_titulo = t.get("titulo", "Sem título")
            
            # Criamos uma chave única para cada tarefa no loop
            with st.container():
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                
                with c1:
                    if is_done:
                        st.markdown(f"✅ <span style='color: gray; text-decoration: line-through;'>{t_titulo}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"⏳ **{t_titulo}**")
                
                with c2:
                    # Se NÃO está concluída, mostra o botão. Se está, o botão DESAPARECE.
                    if not is_done:
                        if st.button("✔", key=f"btn_done_{t_id}"):
                            if TaskService.concluir(t_id, token):
                                # O rerun garante que o loop recomece e 'is_done' seja True, escondendo este botão
                                st.rerun()
                    else:
                        st.write("🌟")

                with c3:
                    if st.button("🗑️", key=f"btn_del_{t_id}"):
                        if TaskService.deletar(t_id, token):
                            st.rerun()
                st.divider()
                
    # NOVA TAREFA (Ajustado para atualizar a lista)
    with st.expander("➕ Adicionar Nova Tarefa", expanded=False):
        with st.form("new_task", clear_on_submit=True):
            titulo = st.text_input("O que vamos realizar hoje?")
            prioridade = st.select_slider("Prioridade", options=["Baixa", "Média", "Alta"], value="Média")
            
            if st.form_submit_button("Agendar Tarefa"):
                if titulo:
                    with st.spinner("Agendando..."):
                        headers = {"Authorization": f"Bearer {token}"}
                        payload = {"titulo": titulo, "prioridade": prioridade}
                        
                        # Fazemos a postagem
                        res = requests.post(f"{API_URL}/tarefas", json=payload, headers=headers)
                        
                        if res.status_code == 200 or res.status_code == 201:
                            st.toast("Tarefa agendada com sucesso!", icon="📅")
                            time.sleep(1) # Essencial para o SQLite no Render processar
                            st.rerun()    # Força a leitura atualizada da lista
                        else:
                            st.error(f"Erro ao salvar: {res.status_code}")
                else:
                    st.warning("Por favor, digite um título para a tarefa.")
    

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
                        # Estilo riscado para tarefas prontas
                        st.markdown(f"✅ <span style='color: gray; text-decoration: line-through;'>{t_titulo}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"⏳ **{t_titulo}**")
                    st.caption(f"Prioridade: {t.get('prioridade', 'Média')}")
                
                with c2:
                    # INTERATIVIDADE: Só mostra o botão se NÃO estiver concluída
                    if not is_done:
                        if st.button("✔", key=f"done_{t_id}", help="Marcar como concluída"):
                            with st.spinner(""): # Pequeno feedback visual de carregamento
                                if TaskService.concluir(t_id, token):
                                    st.toast(f"Concluído: {t_titulo}", icon="✅")
                                    time.sleep(0.5) # Pausa para o usuário ver o toast
                                    st.rerun() # Recarrega para o botão sumir e o texto riscar
                    else:
                        # Se já está pronta, o botão DESAPARECE e mostra uma estrela ou check fixo
                        st.write("🌟")

                with c3:
                    # Botão de excluir sempre disponível
                    if st.button("🗑️", key=f"del_{t_id}", help="Excluir permanentemente"):
                        with st.spinner(""):
                            if TaskService.deletar(t_id, token):
                                st.toast("Removida", icon="🗑️")
                                time.sleep(0.3)
                                st.rerun()
                st.divider()