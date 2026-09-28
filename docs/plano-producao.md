# Evolução para controle de produção

## Objetivo

Conectar solicitação (em cima), produção (embaixo) e coleta/embalagem. Cada pessoa terá uma conta individual. Haverá dois perfis: administrador (patrão) e funcionário; o setor determinará as operações disponíveis.

## Entregas

1. **Base — esta branch:** modelos únicos, autenticação centralizada, configuração, serviços, migrações, cliente HTTP, testes e CI. Mantém tarefas pessoais.
2. **Acessos — implementado nesta branch:** administrador/funcionário, três setores fixos, gerenciamento de funcionários, redefinição e troca de senhas, permissões na API e bootstrap do primeiro administrador. Cada funcionário tem um setor. As ações de produção por setor estão aplicadas na fase 3.
3. **Ordens — implementado nesta branch:** produto/especificação, quantidade/unidade, prazo, prioridade, solicitante, responsável, histórico e etapas `PENDENTE → CORTANDO → COSTURANDO → PRONTO`.
4. **Avisos — implementado nesta branch:** central persistente por destinatário, gerada na mesma transação da conclusão e consultada a cada 10 segundos com sessão ativa. Leitura individual e idempotente não confirma coleta. O aviso mostra situação atual de retirada/cancelamento. A fila de ordens permanece com atualização manual. Sem avisos externos ou geração retroativa.
5. **Piloto:** PostgreSQL e driver, migrações validadas, backup e restauração testados, servidor compartilhado, uso com pessoas dos dois setores.
6. **Indicadores:** tempo por etapa, fila, atrasos, impedimentos e tempo aguardando coleta.

## Regras operacionais e evoluções

- Funcionário não pode administrar contas ou alterar privilégios.
- Administrador pode corrigir/cancelar com justificativa; ordens operacionais terão histórico em vez de exclusão definitiva.
- A troca de etapa deve validar a versão atual da ordem para não sobrescrever alterações concorrentes.
- Repetição da mesma conclusão não cria novo aviso. Se houver reabertura autorizada, uma nova conclusão será outro evento rastreável.
- O aviso permanece disponível no próximo acesso. Painel fechado não receberá push nesta primeira entrega.
- Impedimento não substitui etapa: registra motivo e intervalo em que o trabalho ficou parado.
- Tarefas pessoais antigas não serão convertidas silenciosamente em ordens reais.

## Definições operacionais ainda pendentes

- Quem solicita em cima: patrão, funcionário ou ambos?
- O lote fica pronto por inteiro ou há liberações e coletas parciais?

Premissa inicial: funcionário de solicitação cria ordens; cada ordem tem um lote completo. Confirmar antes de fechar o schema operacional. Essas decisões não bloqueiam a organização da base.

## Fora do escopo inicial

Estoque completo, financeiro, etiquetas, integrações com marketplaces e mensagens externas. Primeiro validar o ciclo solicitar, produzir, avisar e coletar.
