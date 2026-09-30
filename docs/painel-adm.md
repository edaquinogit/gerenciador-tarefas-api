# Todas as tarefas — visão do administrador

Após entrar como administrador, clique no botão **Todas as tarefas**, no topo da página. O item também está no menu lateral. A visão oferece duas abas:

- **Ordens entre setores:** todas as situações por padrão, produto, quantidade, etapa, solicitante, último responsável, prioridade, prazo e atualização. Filtros por etapa e situação incluem ativas, coletadas e canceladas.
- **Tarefas pessoais:** tarefas de todas as contas, inclusive do próprio administrador e de funcionários inativos, com pessoa, setor atual, prioridade e conclusão. Filtro por pendentes/concluídas.

Cada página mostra até 20 registros. Use Anterior e Próxima para consultar os demais. A navegação mostra Página X de Y, total de registros no filtro e intervalo exibido. Os botões ficam desativados nos limites. Se os resultados diminuírem, a página é ajustada automaticamente e os dados são consultados novamente. Trocar filtros volta à primeira página. Registros não são carregados todos de uma vez. Ordens seguem a ordenação operacional por prioridade e prazo; tarefas pessoais aparecem por ID decrescente.

O painel consulta a API a cada **10 segundos enquanto está aberto**, além do botão Atualizar agora. Exibe o horário de cada consulta bem-sucedida no fuso da Bahia. Não usa WebSocket nem garante atualização instantânea: abas suspensas e problemas de rede podem atrasar a consulta. Em falha, mostra erro; não informa que a fila está vazia. O temporizador só reexecuta o painel, sem reenviar formulários de cadastro ou mudança de etapa.

O administrador usa layout amplo, com filtros de ordens lado a lado e tabelas ocupando a largura disponível. Muitas colunas ainda podem exigir rolagem horizontal em telas pequenas.

Esta tela serve para acompanhamento. Para avançar/cancelar/coletar ordens, use Ordens de produção. A consulta global não concede permissão para editar ou excluir tarefas pessoais de terceiros; essas ações continuam com o dono da tarefa. A tela Minhas tarefas informa que o administrador pode acompanhá-las.

Funcionários não veem o botão/menu e a API `GET /admin/tarefas` responde 403 a esses usuários, mesmo em chamada direta. `/tarefas` continua restrita às tarefas do usuário conectado. O painel não exibe telefone, e-mail ou dados de autenticação.

## Teste com duas sessões

1. Admin abre Todas as tarefas; funcionário abre uma sessão independente.
2. Funcionário cria uma tarefa pessoal. Com o painel ativo, confira seu aparecimento na aba correspondente no próximo ciclo de consulta.
3. Produção muda uma ordem de PENDENTE para CORTANDO. Confira etapa e responsável na aba Ordens entre setores.
4. Funcionário conclui sua tarefa; o painel deve mostrar Concluída. Confira filtros e paginação.
5. Interrompa a API durante o ensaio; o painel deve apresentar erro. Reinicie-a e confira recuperação da consulta.

AppTest valida abertura pelo botão, dados novos em nova consulta, filtros e tratamento de erro. O agendamento real de 10 segundos em navegador/dispositivo da empresa deve ser confirmado nesse teste presencial.
