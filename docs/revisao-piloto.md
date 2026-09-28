# Revisão para ensaio entre setores — 28/09/2026

Base revisada: `e939d491ef54e0d5e9b5244b75884b29525249c1` (ordens e avisos). Esta preparação acrescenta um ambiente de demonstração e um roteiro de aceite; não altera as regras de avanço, destinatários ou coleta.

## Resultado e providências

| Ponto revisado | Resultado / providência |
|---|---|
| Separação do banco | O procedimento comum exigia configuração manual. O novo comando usa exclusivamente `.pilot/piloto.db`, sem modificar `.env` ou o banco existente. Teste confirma isolamento mesmo com DATABASE_URL externo definido. |
| Acessos para o ensaio | Quatro contas individuais, setores definidos, senhas aleatórias e cadastro público desativado. Senhas iniciais ficam em arquivo local ignorado pelo Git. |
| Inicialização | Um comando inicia API e interface, verifica migrações/schema e portas e encerra os processos ao sair. A interface só abre na LAN com `--rede`; API fica em loopback. |
| Identificação do teste | Faixa visível antes e depois do login reduz confusão com operação real. |
| Permissões e fluxo | Testes cobrem avanço por setor, sequência de etapas, conflitos de versão, cancelamento e coleta. O novo teste usa contas reais criadas pelo preparador e banco migrado em disco. |
| Avisos | Criação junto da transição para PRONTO, sem duplicação em repetição; leitura individual não coleta o lote. Coleta e leitura persistem. |
| Uso simultâneo | Há proteção de versão e testes de concorrência. Isso não equivale a teste de carga ou validação da rede da empresa. |
| Procedimento humano | Roteiro inclui quatro participantes, reinício, disputa, cancelamento, registro de falhas e critérios de aprovação. |

## Evidências executadas

- Instalação no ambiente Python 3.12 e `pip check` sem dependências incompatíveis.
- Ruff: análise estática e formatação.
- Suíte completa de API, permissões, ordens, transações, avisos, migrações, interface e preparação do ensaio.
- Inicialização real de Uvicorn e Streamlit no ambiente Linux; health HTTP de ambos disponível.
- Login e tela inicial dos quatro perfis via Streamlit AppTest, usando a API real e as senhas geradas, sem mocks do serviço.
- Interrupção do iniciador com SIGINT: API e Streamlit encerrados, portas liberadas.

AppTest não é um navegador físico e não valida o temporizador em dispositivos da empresa. A validação presencial do aviso e da rede consta no roteiro. Windows/WSL e acesso por outros computadores não foram executados neste ambiente. Advertências de depreciação de dependências não impediram os testes.

## Limites para a decisão

Preparado para **ensaio controlado com dados fictícios**. Os PRs anteriores e este continuam sujeitos a revisão; nenhum merge ou deploy na empresa foi executado. A fila exige atualização manual, enquanto a central de avisos consulta a cada 10 segundos com sessão ativa. Não há notificação com o navegador fechado, entrega parcial nem confirmação separada de embalagem.

Antes da operação real: concluir aceite presencial, definir hospedagem protegida e responsáveis, testar backup/restauração e avaliar capacidade para o volume simultâneo esperado. Não usar o resultado local como aprovação desses itens.
