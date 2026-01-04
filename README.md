# 📋 Gerenciador de Tarefas – API REST

API REST desenvolvida em **Python** com **FastAPI** e **SQLModel**, com foco em praticar conceitos de backend como CRUD, persistência em banco de dados, organização de projeto e boas práticas para APIs modernas.

Projeto voltado para aprendizado e demonstração de habilidades iniciais em **desenvolvimento backend**.

---

## 🚀 Tecnologias Utilizadas

- Python 3.11+
- FastAPI
- SQLModel
- SQLAlchemy
- SQLite
- Uvicorn
- Git e GitHub

---

## 📂 Estrutura do Projeto

Gerenciador_API_V2/
│
├── main.py # Ponto de entrada da aplicação (FastAPI)
├── models.py # Modelos e criação das tabelas
├── database.py # Conexão com o banco e sessão
├── database.db # Banco de dados SQLite
├── requirements.txt
├── README.md
└── .venv/

---

## ⚙️ Como Executar o Projeto

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git

cd Gerenciador_API_V2

2️⃣ Criar e ativar o ambiente virtual

python -m venv .venv
.venv\Scripts\activate

3️⃣ Instalar as dependências

pip install -r requirements.txt

4️⃣ Executar a aplicação

uvicorn main:app --reload


📌 Acessar a API

Aplicação:
👉 http://127.0.0.1:8000

Documentação interativa (Swagger):
👉 http://127.0.0.1:8000/docs

🔄 Funcionalidades

Criar tarefas

Listar tarefas

Filtrar tarefas por status

Buscar tarefas por termo no título

Atualizar tarefa (concluir)

Deletar tarefa

🧠 Conceitos Aplicados

Arquitetura básica de API REST

Lifespan do FastAPI

Injeção de dependências

ORM com SQLModel

Boas práticas de versionamento com Git

Commits semânticos

🎯 Objetivo do Projeto

Este projeto faz parte do meu processo de aprendizado em Backend Python, com foco em evolução contínua e preparação para oportunidades como estágio ou desenvolvedor júnior.

📄 Licença

Este projeto está sob a licença MIT.

