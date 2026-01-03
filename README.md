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
