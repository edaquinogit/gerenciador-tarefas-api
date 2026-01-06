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
=======
# Gerenciador de Tarefas API

## 🚀 Sobre o Projeto
O **Gerenciador de Tarefas API** é uma aplicação backend desenvolvida em Python, que permite criar, atualizar, listar e excluir tarefas.  
Este projeto foi desenvolvido como estudo prático de **desenvolvimento de APIs RESTful**, com foco em boas práticas de código, organização de projeto e versionamento no GitHub.  

Ele simula um **sistema de gerenciamento de tarefas**, permitindo aprendizado em:
- Estruturação de APIs RESTful
- Manipulação de dados
- Boas práticas em Python
- Versionamento de código (Git/GitHub)

---

## 📦 Funcionalidades
- Criar novas tarefas (`POST /tarefas`)
- Listar todas as tarefas (`GET /tarefas`)
- Buscar uma tarefa por ID (`GET /tarefas/{id}`)
- Atualizar uma tarefa (`PUT /tarefas/{id}`)
- Deletar uma tarefa (`DELETE /tarefas/{id}`)
- Marcar tarefa como concluída

---

## 🛠 Tecnologias
O projeto utiliza as seguintes tecnologias e bibliotecas:

| Tecnologia | Uso |
|------------|-----|
| Python 3.x | Linguagem principal |
| FastAPI    | Criação de API RESTful |
| Pydantic   | Validação de dados e tipagem |
| Uvicorn    | Servidor ASGI para rodar a API |
| Git        | Controle de versão |

---

## 💻 Como Executar

### Pré-requisitos
- Python 3.10+ instalado
- Git instalado

### Passos
1. Clone o repositório:
```bash
git clone https://github.com/edaquinogit/gerenciador-tarefas-api.git

cd gerenciador-tarefas-api


2. Crie um ambiente virtual:

python -m venv .venv


3. Ative o ambiente virtual:

Windows:
.venv\Scripts\activate

Linux/Mac:
source .venv/bin/activate


4. Instale as dependências:

pip install -r requirements.txt


5. Execute a API:

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

=======
6. Acesse a documentação interativa da API em:

http://127.0.0.1:8000/docs


📄 Estrutura do Projeto
gerenciador-tarefas-api/
│
├── main.py            # Arquivo principal da API
├── models.py          # Modelos Pydantic / Classes
├── routes.py          # Definição das rotas da API
├── crud.py            # Funções de CRUD para tarefas
├── requirements.txt   # Dependências do projeto
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Documentação do projeto


🔧 Endpoints da API
Método	Endpoint	Descrição
GET	/tarefas	Retorna todas as tarefas
GET	/tarefas/{id}	Retorna tarefa específica
POST	/tarefas	Cria uma nova tarefa
PUT	/tarefas/{id}	Atualiza uma tarefa existente
DELETE	/tarefas/{id}	Remove uma tarefa

```
📈 Próximos Passos:

Adicionar autenticação de usuários

Conectar a API a um banco de dados real (PostgreSQL ou SQLite)

Implementar testes automatizados com pytest

Criar documentação detalhada da API e exemplos de uso

Aprimorar endpoints com filtros e paginação

📝 Contato

GitHub: https://github.com/edaquinogit

LinkedIn: https://www.linkedin.com/in/ednaldo-aquino-6536892b5


Desenvolvido como projeto de estudo e portfólio para primeira vaga de emprego Júnio/Estágio.
