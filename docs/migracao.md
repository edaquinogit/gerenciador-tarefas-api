# Migração da base existente

Esta refatoração mantém as tabelas `usuario` e `tarefa` da versão anterior. Não converte tarefas antigas em ordens de produção e acrescenta os campos de acesso na migração `0002`.

## Banco novo

Com `.env` configurado, execute `python -m alembic upgrade head`. Isso cria as tabelas e a versão de migração. A API não executa `create_all` automaticamente.

## Banco SQLite existente

1. Pare a API antiga e qualquer processo que escreva no banco. Não mantenha as duas versões escrevendo ao mesmo tempo.
2. Faça uma cópia de segurança do arquivo e valide que consegue abri-la. Para uma cópia consistente com SQLite, use a API de backup:

```python
import sqlite3

# Escolha um destino novo para não sobrescrever outro backup.
with sqlite3.connect("database.db") as source:
    with sqlite3.connect("database-antes-base.bak") as target:
        source.backup(target)
```

3. Teste primeiro numa cópia, configurando `DATABASE_URL` para essa cópia.
4. Execute `python -m backend.scripts.adotar_banco` na raiz do projeto. O comando compara tabelas, colunas, índices e restrições com os modelos e verifica tarefas órfãs. Recusa bancos divergentes ou já versionados; não tenta corrigir ou apagar dados.
5. Em caso de sucesso, `python -m alembic upgrade head` e `python -m alembic check` devem concluir sem alteração pendente.
6. Confira a quantidade e uma amostra das tarefas, entre com uma conta existente e valide conclusão e listagem. Somente depois repita o procedimento no banco escolhido para uso.

O comando de adoção só registra `0001` depois de validar o schema. Não use `alembic stamp` manualmente para ignorar uma divergência. Se houver diferença, mantenha o original e planeje uma migração específica sobre a cópia.

## Retorno à versão anterior

Não há downgrade destrutivo da baseline. Mantenha juntos o backup, a revisão anterior do código e a configuração compatível. Para voltar, pare o serviço, preserve também uma cópia do banco atual e restaure o backup anterior com o código anterior. Registros criados após o backup precisam de reconciliação; não sobrescreva sem verificá-los.

## Mudanças de execução e comportamento

- Novo comando da API: `python -m uvicorn backend.main:create_app --factory --reload`.
- Imports internos são absolutos; não é preciso ajustar `sys.path` ou `PYTHONPATH`.
- A chave JWT é obrigatória. Se a chave antiga foi pública, substitua-a e faça login novamente.
- Cadastro público fica desabilitado. Crie o primeiro administrador com `python -m backend.scripts.criar_admin --username patrao --telefone "(79) 99999-0001"`; cadastre funcionários pelo painel.
- O antigo script `criar_admin.py`, com senha fixa, foi substituído por um bootstrap interativo. Contas antigas, inclusive uma conta chamada `admin`, migram como funcionários sem setor. O novo administrador pode redefinir suas senhas e atribuir setores. Nenhuma conta existente ganha privilégios pelo nome.
- `POST /tarefas` retorna 201; `/concluir` é idempotente, sem alternância para pendente.
- Conta inativa perde acesso mesmo com um token ainda válido.
- Não existe exclusão de usuário nesta fase. Tarefas não devem ser apagadas automaticamente quando alguém deixar a empresa.


## Upgrade da fase de base (0001) para acessos (0002)

1. Pare a API e faça backup conforme o procedimento acima.
2. Execute `python -m alembic upgrade head`. Não execute adoção de legado em banco já versionado.
3. A migração acrescenta `perfil=FUNCIONARIO`, `setor=NULL` e `token_version=0` às contas existentes. Preserva usuários, hashes, IDs e tarefas. Nenhum usuário é promovido automaticamente.
4. Execute uma única vez o bootstrap do primeiro administrador com a API parada. Se o nome de usuário já existir, escolha outro para a nova conta administrativa.
5. Entre no painel administrativo para classificar os funcionários existentes e redefinir senhas antigas quando necessário.
6. Todos precisam entrar novamente: tokens emitidos antes desta versão não possuem a versão de sessão exigida.

Desativação e redefinição de senha não removem tarefas. Reativar não torna tokens anteriores válidos. O downgrade que apagaria perfis e setores é recusado; para reverter, siga o procedimento de backup e reconciliação.


## Upgrade para ordens compartilhadas (0003)

Pare a API, faça backup e execute `python -m alembic upgrade head`, seguido de `python -m alembic check`. A migração cria somente `ordem` e `eventoordem`, incluindo chaves estrangeiras e unicidade de envio/versão. Usuários, setores, hashes, tarefas e sessões da fase 0002 são preservados. Tarefas pessoais não são convertidas em ordens.

Valide o ciclo com contas de solicitação, produção e coleta em um banco de teste antes do uso operacional. O downgrade destrutivo que apagaria o histórico é recusado; uma reversão exige backup e reconciliação.


## Upgrade para avisos (0004)

Pare a API, faça backup e execute `python -m alembic upgrade head` e `python -m alembic check`. A nova tabela `notificacao` preserva ordens e histórico existentes. Na migração original não havia avisos retroativos; a revisão 0008 recupera avisos ausentes de conclusões registradas. Conclusões posteriores geram avisos persistentes na mesma transação; teste o recebimento com o solicitante e o ADM e acompanhe a coleta pela fila. A coleta é independente da leitura de avisos. Consulte docs/avisos.md.


## Upgrade para telefone (0005)

Para sua instalação que já mostra `0004 (head)`, **não execute novamente criar_admin** e não apague o banco. Antes de atualizar, pare API e Streamlit, faça o backup descrito acima e preserve a revisão anterior do código. Aplique e teste primeiro em uma cópia.

Depois de atualizar a branch `main` (`git switch main` e `git pull --ff-only origin main`), com ambiente virtual ativado e na raiz do projeto:

```bash
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

A revisão desta etapa histórica é `0005`; na versão atual, o resultado esperado é `0008 (head)` e nenhuma mudança de schema pendente. Reinicie API e interface com os comandos do README. Entre com o **mesmo usuário e senha**. Complete seu contato em Minha conta; novos funcionários pedem telefone com DDD. No topo da tela administrativa, clique em **Painel de produção**.

A migração acrescenta telefone nulo às contas existentes e torna e-mail opcional, sem apagar e-mails anteriores. Preserva IDs, senhas, perfis, setores, versões de sessão, tarefas, ordens, eventos e avisos. No SQLite, a alteração exige reconstruir a tabela de usuários: as chaves estrangeiras são desativadas somente na conexão de migração, e as referências são verificadas antes do commit. Se houver referências inválidas, a transação é revertida e a migração falha. Nas conexões da aplicação as verificações permanecem ativas.

O contrato de cadastro mudou: atualize clientes da API de `email` para `telefone`. Não execute interface antiga contra API nova nem o contrário. Não existe conversão de e-mail em telefone nem preenchimento fictício de contas reais.

Para o ensaio `.pilot`, estes comandos comuns leem `.env` e **não devem ser usados para tentar atualizar seu banco de demonstração**. Preserve a pasta `.pilot` completa fora do repositório, com serviços parados, e prepare um novo ensaio pelo comando `piloto preparar`, conforme docs/piloto.md. Guarde a versão anterior junto dos dados se precisar retomar o ensaio antigo.


## Upgrade para sessões (0007)

Pare API e Streamlit, execute `python -m backend.scripts.backup_sqlite` e só prossiga após sucesso. Execute `python -m alembic upgrade head` e `python -m alembic check`. A migração cria `sessao`, preservando usuários, ordens, tarefas, histórico e avisos. Tokens antigos exigem novo login. Reinicie os dois serviços. Configuração do cookie, LAN/HTTPS e comandos completos em [sessões e experiência](sessoes-experiencia.md).


## Upgrade para regras operacionais (0008)

Cria `autorizacaosenha` e recupera avisos ausentes de conclusões existentes, sem apagar registros. Pare serviços, faça backup e siga [regras operacionais](regras-operacionais.md). Avisos antigos da coleta são filtrados na API. Não converte tarefas pessoais em ordens.
