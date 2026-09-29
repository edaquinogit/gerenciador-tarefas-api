# Gerenciador de tarefas — base para controle de produção

Aplicação Python com **FastAPI**, **Streamlit** e **SQLModel**. Esta etapa organiza a base existente para a futura operação de solicitação, corte, costura e coleta.

**Disponível agora:** cadastro por telefone com DDD, painel global do administrador com atualização a cada 10 segundos, administrador e funcionários, setores, ordens compartilhadas, corte/costura/pronto, confirmação de coleta, cancelamento com justificativa, histórico, avisos automáticos de produtos prontos e tarefas pessoais. Inclui gestão de contas, troca de senhas, JWT, migrações e testes. Usuários inativos não conseguem entrar nem reutilizar tokens. Alterações administrativas de conta e trocas de senha revogam sessões anteriores; atualizar o próprio telefone mantém a sessão.

**Ainda não implementado:** avisos externos (WhatsApp/e-mail/push), atualização periódica da tela operacional de ordens, lotes parciais e edição/reabertura de ordens. O painel **Todas as tarefas** do administrador e a central de avisos se atualizam a cada 10 segundos com sessão ativa. Esta versão ainda não deve ser usada como controle da produção da empresa. Veja [o guia de ordens](docs/ordens.md), [os avisos](docs/avisos.md) e [o plano de evolução](docs/plano-producao.md).

## Ensaio entre setores

Para testar com quatro contas, banco separado e inicialização em um único terminal, siga [o roteiro prático](docs/piloto.md). A branch `feat/telefone-painel-adm` reúne as etapas anteriores para esse ensaio.

## Atualização de uma instalação existente

A versão 2.5 substitui `email` por `telefone` nos cadastros e respostas da API. Com os serviços parados, faça backup e aplique a migração `0005` antes de reiniciar. Veja [a atualização para telefone](docs/migracao.md#upgrade-para-telefone-0005) e [o painel geral](docs/painel-adm.md). Não recrie o administrador existente.

## Executar localmente

Requer Python 3.11 ou 3.12. Execute os comandos na raiz do repositório.

```bash
python -m venv .venv
```

Ative o ambiente:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows CMD: `.venv\Scripts\activate.bat`
- Linux/macOS: `source .venv/bin/activate`

```bash
python -m pip install -r requirements-dev.txt
python -c "from pathlib import Path; import secrets; p=Path('.env'); p.exists() or p.write_text(Path('.env.example').read_text().replace('SECRET_KEY=', 'SECRET_KEY='+secrets.token_urlsafe(48), 1))"
```

O comando de configuração não sobrescreve um `.env` existente. Nesse caso, revise o arquivo e gere uma nova `SECRET_KEY` com `python -c "import secrets; print(secrets.token_urlsafe(48))"`. A aplicação exige chave com pelo menos 32 caracteres e não possui segredo padrão. Uma troca de chave invalida tokens anteriores.

### Banco novo

```bash
python -m alembic upgrade head
python -m backend.scripts.criar_admin --username patrao --telefone "(79) 99999-0001"
```

O comando cria o **primeiro administrador**, solicita senha e confirmação no terminal e recusa execução quando já existe um administrador. Execute uma única instância com a API parada. Não há senha fixa nem promoção automática de uma conta antiga com nome `admin`. Se o nome de usuário já existir, use outro cadastro para o administrador.

Entre no Streamlit e abra **Funcionários e setores** para cadastrar funcionários, atribuir setor, ativar/desativar e redefinir senhas. Veja [o guia de acessos](docs/acessos.md).

**Banco com dados existentes:** siga primeiro [o procedimento de migração](docs/migracao.md). Não rode a criação inicial sobre tabelas legadas e não exclua o banco para resolver erros.

### API e interface

Terminal 1:

```bash
python -m uvicorn backend.main:create_app --factory --reload
```

Terminal 2, também com o ambiente virtual ativado e na raiz:

```bash
python -m streamlit run frontend/app.py
```

- Interface: http://localhost:8501
- Documentação da API: http://localhost:8000/docs
- Verificação do processo: http://localhost:8000/health (não verifica conectividade com o banco)

A interface usa `API_URL` do ambiente ou do `.env`; em deploy Streamlit, configure essa variável no servidor da interface. Não depende de `secrets.toml` nesta etapa.

## Configuração

| Variável | Uso |
|---|---|
| `SECRET_KEY` | Segredo JWT obrigatório, mínimo 32 caracteres |
| `DATABASE_URL` | Padrão `sqlite:///database.db`, relativo à raiz de execução |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade positiva do token; padrão 60 minutos |
| `ALLOW_REGISTRATION` | Padrão `false`; cadastro público pela API só para desenvolvimento quando habilitado |
| `CORS_ORIGINS` | Lista JSON de origens permitidas; vazia por padrão |
| `API_URL` | URL da API vista pelo processo Streamlit |

O Streamlit se comunica com a API no servidor. CORS não é necessário para essa comunicação. Para outro cliente web, declare apenas as origens utilizadas.

O `.env` anteriormente versionado foi retirado desta branch, mas permanece no histórico do Git. Substitua qualquer segredo real que tenha sido usado nele. O executável `ngrok.exe` também foi removido; a execução local não depende dele.

## Organização

| Diretório | Responsabilidade |
|---|---|
| `backend/api/` | Rotas e contratos HTTP |
| `backend/models/` | Definição única das tabelas |
| `backend/schemas/` | Dados de entrada e saída, sem expor hashes |
| `backend/services/` | Operações de usuários e tarefas |
| `backend/core/` | Configuração e autenticação |
| `backend/database/` | Conexão e sessão por requisição |
| `backend/scripts/` | Cadastro local e adoção do banco legado |
| `frontend/` | Interface Streamlit e cliente HTTP |
| `migrations/` | Evolução versionada do banco |
| `tests/` | API, interface, configuração e migrações |

O banco não é recriado no início da API. Migrações são executadas explicitamente. O schema desta fase preserva os campos existentes, incluindo `concluido`, IDs e hashes bcrypt. A migração `0002` acrescenta perfil, setor e versão de sessão; `0003` cria ordens e histórico; `0004` acrescenta avisos persistentes; `0005` adiciona telefone e torna o e-mail legado opcional, preservando os valores existentes.

## Contratos HTTP

| Método e caminho | Comportamento |
|---|---|
| `POST /token` | Login por formulário; retorna JWT |
| `GET /usuarios/me` | Dados do próprio usuário, incluindo telefone |
| `PATCH /usuarios/me/telefone` | Atualizar o próprio contato |
| `GET /admin/tarefas` | Consulta global paginada, somente administrador |
| `POST /usuarios` | Cadastro de desenvolvimento, se habilitado; sempre funcionário sem setor |
| `GET /setores` | Catálogo fixo de setores, exige login |
| `GET/POST /admin/funcionarios` | Listar/criar funcionários, somente administrador |
| `PATCH /admin/funcionarios/{id}` | Definir setor e ativação, somente administrador |
| `POST /admin/funcionarios/{id}/senha` | Redefinir senha de funcionário, somente administrador |
| `POST /usuarios/me/senha` | Alterar a própria senha, exigindo a senha atual |
| `GET /tarefas` | Lista somente tarefas do usuário conectado |
| `POST /tarefas` | Cria tarefa; retorna 201 |
| `PATCH /tarefas/{id}/concluir` | Define concluído como verdadeiro; repetir não reabre |
| `DELETE /tarefas/{id}` | Exclui tarefa pessoal; UI solicita confirmação |

Título deve conter de 1 a 200 caracteres; prioridades aceitas: `Baixa`, `Média`, `Alta`. Cliente não pode atribuir `usuario_id` ou `concluido` durante a criação. Registros existentes mantêm seus valores. A exclusão continua restrita às tarefas pessoais. Ordens de produção usam cancelamento com histórico.

## Validação

```bash
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

Os testes utilizam banco isolado em memória ou arquivos temporários. Não usam o banco configurado pelo usuário. A CI executa os mesmos comandos em Python 3.11 e 3.12.

As dependências diretas estão fixadas por ambiente; as transitivas ainda são resolvidas pelo pip. SQLite é a base validada nesta etapa. PostgreSQL, backup operacional e implantação definitiva ainda não foram validados. O ensaio controlado em rede local usa apenas dados fictícios e SQLite isolado; veja o roteiro acima.
