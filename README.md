# 🎯 Pro Task Manager - Full-Stack Application

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLModel](https://img.shields.io/badge/SQLModel-Latest-black?style=flat)](https://sqlmodel.tiangolo.com/)

O **Pro Task Manager** é uma solução completa para gerenciamento de tarefas, desenvolvida para demonstrar a integração entre uma API robusta em **FastAPI** e um frontend interativo em **Streamlit**. O projeto foca em segurança, utilizando autenticação JWT e uma arquitetura organizada em camadas.

---

## 🚀 Funcionalidades

- **Sistema de Autenticação:** Registro de novos usuários e login seguro com JWT (JSON Web Tokens).
- **CRUD de Tarefas:** Criação, listagem, conclusão (check) e exclusão de tarefas.
- **Painel de Progresso:** Visualização dinâmica do percentual de conclusão das tarefas com efeitos visuais (balloons).
- **Priorização:** Classificação de tarefas por níveis de urgência (Baixa, Média, Alta).
- **Validação de Cadastro:** Implementação de Captcha matemático para evitar bots no registro.

---

## 🛠️ Tecnologias Utilizadas

### **Backend**
- **FastAPI:** Framework web de alta performance.
- **SQLModel (SQLAlchemy + Pydantic):** Para interação simplificada com o banco de dados.
- **SQLite:** Banco de dados relacional leve e eficiente.
- **Passlib & Bcrypt:** Para hashing seguro de senhas.
- **PyJWT:** Geração e validação de tokens de acesso.

### **Frontend**
- **Streamlit:** Framework para criação de interfaces web rápidas e intuitivas.
- **Requests:** Para comunicação assíncrona com a API.
- **Python Dotenv:** Gerenciamento de variáveis de ambiente.

---

## 🏗️ Arquitetura do Projeto

O projeto segue uma estrutura de separação de responsabilidades para facilitar a manutenção e evolução:

```text
📂 Gerenciador_API_V2
├── 📂 backend           # API, Modelos e Lógica de Negócio
│   ├── 📂 models       # SQLModel Tables e Schemas
│   ├── 📂 auth         # Lógica de JWT e Criptografia
│   └── main.py         # Entrypoint do Servidor Uvicorn
├── 📂 frontend          # Interface do Usuário
│   └── app.py          # Aplicação Streamlit e Service Layer
└── database.db         # Banco de Dados SQLite (gerado automaticamente)

🔧 Como Executar

1. Clonar o repositório

git clone
 [https://github.com/edaquinogit](https://github.com/edaquinogit/gerenciador-tarefas-api)

cd SEU_REPOSITORIO

Configurar o ambiente

python -m venv .venv

source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt

3. Rodar o Backend


$env:PYTHONPATH = "."

python -m uvicorn backend.main:app --reload

4. Rodar o Frontend

streamlit run frontend/app.py

📈 Próximas Evoluções (Roadmap)
[ ] Implementar filtros de tarefas por prioridade e status.

[ ] Adicionar campo de data limite (deadline) com notificações.

[ ] Realizar deploy automatizado no Render (Backend) e Streamlit Cloud (Frontend).

[ ] Implementar testes unitários com Pytest.

✒️ Autor
Ednaldo - Desenvolvedor em evolução -
www.linkedin.com/in/ednaldo-aquino-6536892b5
