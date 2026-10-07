# Avisos automáticos de produtos prontos

Quando a produção confirma **Pronto**, a API registra um aviso individual para:

- O solicitante da ordem, se estiver ativo.
- Cada administrador ativo.

Uma pessoa que atende mais de um critério recebe um único aviso. Funcionários de produção e outros solicitantes não recebem avisos dessa ordem, salvo se forem o próprio solicitante. Os destinatários são definidos no momento da conclusão; contas criadas/ativadas depois não recebem avisos antigos automaticamente, mas podem consultar a fila de ordens.

## Uso

A central **Avisos de produtos prontos** aparece nas páginas de usuários habilitados a consultar ordens. Ela consulta a API a cada 10 segundos enquanto a sessão estiver ativa, destacando e expandindo avisos não lidos, mostrando número da ordem, produto, quantidade e horário. Use **Marcar como lido** para reconhecer um aviso ou **Incluir avisos lidos** para consultar o histórico. A paginação mostra 10 avisos por página.

O aviso não depende de a pessoa estar conectada no momento da conclusão. Ele fica salvo no banco e aparece no próximo login. Não há envio de WhatsApp, e-mail, som ou push com navegador fechado nesta versão. A consulta periódica pode ser atrasada pelo navegador/rede se a aba estiver em segundo plano.

A central e a fila são atualizadas automaticamente a cada 10 segundos, sem reexecutar os formulários ou o diálogo aberto. **Atualizar fila** antecipa a consulta; ao receber um aviso, use **Abrir ordem** para consultar o lote.

## Leitura e retirada são ações diferentes

Marcar um aviso como lido:

- Atualiza somente o aviso daquele destinatário.
- Não marca o aviso de outras pessoas como lido.
- Não confirma coleta nem modifica a versão da ordem.
- Preserva a data da primeira leitura se a ação for repetida.

A coleta é confirmada na ordem pelo setor autorizado. A central consulta também a situação atual da ordem: se já houve coleta ou cancelamento, informa isso e não apresenta o lote como disponível. O texto histórico registra que a ordem ficou pronta no passado.

## Consistência e acesso

Conclusão, evento de histórico e avisos são persistidos na mesma transação. Se o armazenamento de um aviso falhar, a conclusão não é efetivada. Versão da ordem e unicidade de evento/destinatário impedem avisos duplicados por requisições repetidas ou concorrentes.

Listagem, contagem e leitura são restritas ao usuário autenticado. Nem o administrador pode marcar avisos de outro usuário como lidos. Contas inativas não acessam a central. A API também filtra avisos legados: somente o próprio solicitante ou um administrador pode ver um aviso destinado à sua conta.

## Migração e API

Após backup e com a API parada:

```bash
python -m alembic upgrade head
python -m alembic check
```

A migração `0004` criou `notificacao`. A migração **0008** recupera destinatários ausentes a partir dos eventos de conclusão existentes, preservando avisos lidos e sem duplicação. Consulte [regras operacionais](regras-operacionais.md).

| Rota | Operação |
|---|---|
| `GET /notificacoes` | Contagem de não lidos e lista pessoal; parâmetros `somente_nao_lidas`, `offset`, `limit` |
| `PATCH /notificacoes/{id}/lida` | Registra leitura individual e idempotente |

Os horários da API usam UTC; a interface mostra o fuso da Bahia. A leitura da caixa nunca grava ou dispara notificações. Uma falha de conexão é apresentada como erro, não como caixa vazia.
