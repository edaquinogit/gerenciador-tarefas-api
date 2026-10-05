# Evolução para controle de produção

## Objetivo

Conectar solicitação (em cima), produção (embaixo) e coleta/embalagem. Cada pessoa terá uma conta individual. Haverá dois perfis: administrador (patrão) e funcionário; o setor determinará as operações disponíveis.

## Entregas

1. **Base — esta branch:** modelos únicos, autenticação centralizada, configuração, serviços, migrações, cliente HTTP, testes e CI. Mantém tarefas pessoais.
2. **Acessos — implementado nesta branch:** administrador/funcionário, três setores fixos, gerenciamento de funcionários, redefinição e troca de senhas, permissões na API e bootstrap do primeiro administrador. Cada funcionário tem um setor. As ações de produção por setor estão aplicadas na fase 3.
3. **Ordens — implementado nesta branch:** produto/especificação, quantidade/unidade, prazo, prioridade, solicitante, responsável, histórico e etapas `PENDENTE → CORTANDO → COSTURANDO → PRONTO`.
4. **Avisos — implementado nesta branch:** central persistente por destinatário, gerada na mesma transação da conclusão e consultada a cada 10 segundos com sessão ativa. Leitura individual e idempotente não confirma coleta. O aviso mostra situação atual de retirada/cancelamento. A fila de ordens permanece com atualização manual. Sem avisos externos ou geração retroativa.
5. **Ensaio controlado — preparado:** banco SQLite isolado, quatro contas, inicialização local/LAN e roteiro de aceite. Atualização atual acrescenta telefone com DDD e acesso do administrador ao painel Todas as tarefas, consultado a cada 10 segundos. Falta registrar o teste presencial com os setores.
6. **Preparação operacional — pendente:** hospedagem protegida, backup/restauração testados, validação de rede e capacidade. Avaliar PostgreSQL e driver conforme a concorrência observada; PostgreSQL não foi implantado ou validado.
7. **Indicadores — pendente:** tempo por etapa, fila, atrasos, impedimentos e tempo aguardando coleta.

## Regras operacionais e evoluções

- Funcionário não pode administrar contas ou alterar privilégios.
- Administrador pode cancelar ordens com justificativa; edição/reabertura ainda não estão implementadas. Ordens operacionais têm histórico em vez de exclusão definitiva.
- Administrador pode consultar tarefas pessoais de todos no painel; cada pessoa continua responsável por alterar/concluir/excluir suas próprias tarefas.
- A troca de etapa deve validar a versão atual da ordem para não sobrescrever alterações concorrentes.
- Repetição da mesma conclusão não cria novo aviso. Se houver reabertura autorizada, uma nova conclusão será outro evento rastreável.
- O aviso permanece disponível no próximo acesso. Painel fechado não receberá push nesta primeira entrega.
- Impedimento não substitui etapa: registra motivo e intervalo em que o trabalho ficou parado.
- Tarefas pessoais antigas não serão convertidas silenciosamente em ordens reais.

## Premissas para confirmar no ensaio

- Quem solicita em cima: patrão, funcionário ou ambos?
- O lote fica pronto por inteiro ou há liberações e coletas parciais?

Premissa inicial: funcionário de solicitação cria ordens; cada ordem tem um lote completo. Confirmar antes de fechar o schema operacional. A implementação atual permite solicitação por funcionário desse setor e pelo administrador; não suporta lotes parciais.

## Fora do escopo inicial

Estoque completo, financeiro, etiquetas, integrações com marketplaces e mensagens externas. Primeiro validar o ciclo solicitar, produzir, avisar e coletar.


## Próximo passo de aceite

Atualizar a instalação para 0008 com backup, completar telefone do administrador e cadastrar um funcionário de cada setor. Executar o roteiro docs/piloto.md com dados fictícios, verificar o painel administrativo durante mudanças feitas por outra pessoa e registrar falhas/tempos observados. Só depois desse aceite avançar para a preparação operacional; a passagem dos testes automatizados não substitui o teste na empresa.


## Categorias — implementado

Classificação automática, agrupamento visual e filtro antes da paginação; pedidos continuam independentes. Migração 0006 mantém ordens existentes em Outros. Incluído backup SQLite consistente com teste de restauração. O aceite presencial, a política de cópias externas e a hospedagem operacional seguem pendentes. Consulte docs/categorias.md.


## Continuidade de uso — implementada na versão 2.6

Sessões revogáveis com recuperação após F5, renovação limitada, restauração de navegação e rascunho de nova ordem, paginação dos avisos e tema consistente. Migração 0007. Consulte [sessões e experiência](sessoes-experiencia.md). O próximo marco continua sendo o aceite presencial entre setores, incluindo refresh, rede e logout nos dispositivos reais.


## Operação por ordens — versão 2.7

Interface sem tarefas pessoais, avisos privados recuperados na migração 0008, autorização individual de senha pelo ADM, cards por prioridade/prazo e filtros compactos. Critérios de aceite em [regras operacionais](regras-operacionais.md).
