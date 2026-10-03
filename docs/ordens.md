# Ordens compartilhadas entre setores

## Operação básica

1. **Solicitação:** entre com a conta do setor, abra **Ordens de produção** e envie produto, especificação, quantidade, unidade, prioridade e prazo. Cada envio cria um número de ordem e registra o solicitante.
2. **Produção:** a mesma ordem aparece na fila. Use **Iniciar corte**, **Iniciar costura** e **Marcar lote pronto**, nessa ordem.
3. **Solicitação/coleta:** quando consultar a fila, uma ordem pronta aparece com destaque de produto disponível. O setor de coleta abre por padrão o filtro **Pronto**.
4. **Coleta e embalagem:** confirme que retirou todo o lote e clique em **Confirmar coleta**. A ordem sai das ativas e continua acessível no filtro **Coletadas**.

**A fila é atualizada manualmente** pelo botão **Atualizar fila**. A central de avisos já recebe automaticamente os produtos prontos, consultando a API a cada 10 segundos com a sessão ativa, sem recarregar formulários. Os avisos persistem para o próximo login; não há push com a tela fechada. Consulte [o guia de avisos](avisos.md).

Cada ordem representa um lote inteiro, em peças ou kits. Não há liberação parcial. O horário é mostrado no fuso da Bahia e armazenado em UTC.

## Permissões

| Ação | Solicitação | Produção | Coleta/embalagem | Administrador |
|---|---|---|---|---|
| Ver ordens e histórico | Sim | Sim | Sim | Sim |
| Criar ordem | Sim | Não | Não | Sim |
| Avançar corte/costura/pronto | Não | Sim | Não | Sim |
| Confirmar coleta | Não | Não | Sim | Sim |
| Cancelar com justificativa | Não | Não | Não | Sim |

Funcionário sem setor não acessa ordens compartilhadas. A API verifica essas permissões; esconder botões não é a proteção de acesso. Esta aplicação atende uma empresa; não há isolamento entre empresas.

Os funcionários de produção compartilham a mesma fila; não há atribuição exclusiva. Cada avanço registra quem executou a ação, e essa pessoa aparece como responsável pela última etapa. O histórico identifica todos os envolvidos.

## Regras e limites

- Etapas: `PENDENTE → CORTANDO → COSTURANDO → PRONTO`. Não é permitido pular ou retroceder.
- A confirmação de coleta é separada da etapa pronto; o status permanece pronto e os campos de coleta registram pessoa/horário.
- Cancelamento exige justificativa de pelo menos 5 caracteres e não apaga a ordem. Ordens canceladas ou coletadas não aceitam novas alterações.
- Não existe exclusão, reabertura ou edição de produto/quantidade/prazo após o envio. Para corrigir um envio errado, o administrador cancela com justificativa e a solicitação cria outra ordem.
- Cada alteração exige a versão lida da ordem. Se outra pessoa agir primeiro, a API responde 409 e solicita atualização da fila.
- A interface reutiliza o identificador de envio numa tentativa repetida. A API registra um único evento para a mesma operação. Reutilizar identificador com outros dados retorna conflito.
- Alteração e histórico são gravados na mesma transação. Uma falha ao gravar histórico não pode deixar a etapa avançada.
- Tarefas pessoais antigas são preservadas no banco e retiradas dos menus. Não são transformadas em ordens reais.
- A fila mostra 20 itens por página, primeiro urgentes e depois prazo/ID. Filtros: etapa e ativas/coletadas/canceladas/todas. A página pode ser alterada manualmente; ao trocar filtros, volte à página 1 se necessário.

## API

| Método/caminho | Operação |
|---|---|
| `POST /ordens` | Criar ordem, com `request_id` UUID |
| `GET /ordens` | Lista compartilhada; filtros `status`, `situacao`, `offset`, `limit` |
| `GET /ordens/{id}` | Consultar ordem |
| `GET /ordens/{id}/historico` | Histórico em ordem de versão |
| `PATCH /ordens/{id}/etapa` | Enviar `status`, `versao` e `request_id` |
| `POST /ordens/{id}/coleta` | Enviar `versao` e `request_id` |
| `POST /ordens/{id}/cancelamento` | Enviar `motivo`, `versao` e `request_id` |

Quantidade inteira positiva; unidades `pecas` ou `kits`; prioridade `NORMAL` ou `URGENTE`. O prazo na API precisa incluir fuso horário. A resposta converte horários para UTC com indicação de fuso. IDs de autor, etapa inicial e versão são definidos pelo servidor.

## Atualizar a instalação

Com a API parada e backup conferido, execute na raiz:

```bash
python -m alembic upgrade head
python -m alembic check
```

A migração `0003` cria `ordem` e `eventoordem`, sem modificar os registros de usuários ou tarefas. Inicie a API e o Streamlit conforme o README. Valide primeiro com contas de teste de cada setor. Não houve validação de PostgreSQL ou implantação real nesta etapa.


## Navegação da fila

A tela operacional e o painel administrativo usam Anterior/Próxima com até 20 registros, Página X de Y e total filtrado. Ao mudar filtros, voltam à primeira página; se coleta/cancelamento reduzir a lista, ajustam a página e consultam novamente. Na produção, urgentes de qualquer categoria aparecem antes das normais. Os grupos normais e suas contagens continuam relativos à página exibida.

A interface utiliza `GET /ordens/pagina`, que retorna `{total, itens}` com os mesmos filtros e permissões. `GET /ordens` mantém o retorno em lista para compatibilidade. Esta correção não exige migração: o schema continua em 0006. Atualize e reinicie API e Streamlit juntos. A paginação por posição pode mudar quando outras pessoas alteram a fila; o painel é uma consulta atual, não uma fotografia imutável dos registros.
