# Migração da base existente

Esta refatoração mantém as tabelas `usuario` e `tarefa` da versão anterior. Não converte tarefas antigas em ordens de produção e não acrescenta perfis de acesso.

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
- Cadastro público fica desabilitado. Crie contas com `python -m backend.scripts.criar_usuario`.
- O script antigo `criar_admin.py` foi removido: criava uma conta com senha fixa, sem privilégio administrativo real. Uma conta previamente criada por ele permanece no banco e precisa ter a senha substituída antes de qualquer exposição.
- `POST /tarefas` retorna 201; `/concluir` é idempotente, sem alternância para pendente.
- Conta inativa perde acesso mesmo com um token ainda válido.
- Não existe exclusão de usuário nesta fase. Tarefas não devem ser apagadas automaticamente quando alguém deixar a empresa.
