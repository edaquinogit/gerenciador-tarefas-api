# 🚀 Gerenciador de Tarefas API

API RESTful desenvolvida com **FastAPI** e **SQLModel** para gerenciamento de tarefas, com autenticação JWT, CRUD completo e integração com frontend em **Streamlit**.

---

## 📂 Estrutura do Projeto

Gerenciador_API_V2/ ├── backend/ │   ├── core/              # segurança, autenticação, config │   ├── database/          # conexão e modelos SQLModel │   ├── schemas/           # entrada/saída de dados (Pydantic) │   ├── scripts/           # utilitários (criar admin, resetar DB) │   ├── services/          # lógica de negócio (tarefas, usuários) │   ├── test/              # testes automatizados │   ├── main.py            # ponto de entrada da API │   └── requirements.txt   # dependências do backend ├── frontend/ │   ├── app.py             # Streamlit app │   └── .streamlit/secrets.toml ├── README.md ├── LICENSE ├── .gitignore


---

## ⚙️ Tecnologias Utilizadas

- Python 3.11+
- FastAPI
- SQLModel
- SQLite (local)
- Streamlit
- Pytest
- JWT (autenticação)

---

## 🚀 Como Executar Localmente

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload

Acesse: http://localhost:8000/docs

Frontend

cd frontend
streamlit run app.py


Acesse: http://localhost:8501


🔐 Autenticação

- Login via JWT Token
- Rotas protegidas com Depends(get_current_user)
- Exemplo de login:
POST /login
{
  "username": "admin",
  "password": "123456"
}

🧪 Testes

cd backend
pytest

🌐 Deploy
- Backend: Render / Railway
- Frontend: Streamlit Cloud
- Variáveis de ambiente necessárias:
- DATABASE_URL
- SECRET_KEY
- API_BASE_URL

📌 Funcionalidades
- [x] Criar tarefa
- [x] Listar tarefas
- [x] Atualizar tarefa
- [x] Deletar tarefa
- [x] Autenticação de usuário
- [ ] Deploy público
- [ ] Dashboard com Streamlit

📬 Contato
Desenvolvido por Ednaldo Aquino
- LinkedIn 
(www.linkedin.com/in/ednaldo-aquino-6536892b5)

- GitHub 
(https://github.com/edaquinogit)

---




