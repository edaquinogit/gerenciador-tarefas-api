# Operação por ordens — versão 2.7

## O que muda

- “Minhas tarefas” e a aba de tarefas pessoais saem da interface de todos os perfis. Dados e APIs legadas são preservados; tarefas pessoais não são convertidas em ordens. Navegação antiga é redirecionada sem descartar filtros ou rascunhos.
- Ordens aparecem em cards: título clicável, prioridade, quantidade, categoria, etapa e prazo. Urgente usa vermelho e texto; normal usa azul. Prazo vencido tem indicação separada, sem mudar a prioridade. Pronto usa verde. Duas colunas no computador e uma em telas pequenas.
- Clique no título do card ou em “Abrir ordem” no aviso para acessar detalhes, histórico e ações autorizadas. O detalhe consulta a situação atual na API. A confirmação explícita de coleta permanece obrigatória.
- Etapas ficam em uma faixa horizontal rolável manualmente. Categoria e situação ficam em “Mais filtros”. Limpar filtros restaura o padrão do setor; alterações retornam à primeira página. Ordenação global: urgentes, prazo e ID, antes da paginação. Categoria deixa de reagrupar a fila, preservando a ordem dos prazos.
- Filtros, rascunho confirmado e identificação da ordem aberta são recuperados após F5 enquanto a sessão for válida.

## Produtos prontos

Somente o solicitante daquela ordem e os administradores ativos recebem um aviso. Listagem, contagens e leitura verificam o destinatário e a titularidade atual no servidor. Avisos antigos encaminhados ao setor de coleta continuam armazenados, mas não são exibidos nem podem ser marcados como lidos por destinatários que não sejam o solicitante ou ADM.

A caixa mostra um destaque quando há avisos não lidos e inicia expandida. Atualiza a cada 10 segundos com a página ativa. A fila operacional permanece compartilhada entre setores; coleta consulta as ordens prontas nessa fila. Ler um aviso não confirma retirada. Avisos de ordens já coletadas/canceladas mostram a situação atual.

A migração 0008 recupera avisos ausentes para solicitantes e administradores ativos a partir de eventos de conclusão existentes. Preserva avisos já lidos e não duplica evento/destinatário. Não inventa eventos ausentes: registros sem evento de conclusão exigem conferência separada.

## Alteração de senha

1. Funcionário abre Minha conta e solicita a troca.
2. ADM vê o pedido em Funcionários e setores → Autorizações de senha, atualizado a cada 10 segundos.
3. ADM permite uma troca por 30 minutos, recusa ou revoga uma liberação.
4. O formulário aparece automaticamente para o funcionário autorizado. Exige senha atual e confirmação da nova senha.
5. A troca consome a permissão na mesma transação e invalida as sessões anteriores. Uma segunda troca exige nova autorização.

Permissão é individual, expira no servidor e não é armazenada como preferência de tela. Senha atual incorreta não consome a liberação. Redefinição pelo ADM e alteração administrativa da conta revogam liberações anteriores. O ADM altera a própria senha sem aprovação e pode redefinir a de funcionários pelo painel. O banco guarda o estado mais recente, datas, versão e administrador responsável pela decisão; não é um histórico completo de todas as solicitações.

## Atualização no Windows / CMD

Pare API e Streamlit com Ctrl+C. Com o ambiente virtual ativado:

```bat
git switch main
git pull --ff-only origin main
python -m pip install -r requirements-dev.txt
python -m backend.scripts.backup_sqlite
```

Após backup bem-sucedido:

```bat
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m uvicorn backend.main:create_app --factory --reload
```

Revisão esperada: **0008**. Em outro terminal na mesma pasta, ative a venv e execute `python -m streamlit run frontend/app.py`. Abra http://127.0.0.1:8501. Preserve `.env`, banco e cadastros existentes. Configuração LAN/HTTPS: [sessões e experiência](sessoes-experiencia.md).

## Aceite entre setores

- Dois solicitantes criam ordens diferentes; produção avança até Pronto. Cada solicitante vê somente seu aviso; ADM vê ambos; produção/coleta não recebem avisos de terceiros.
- Sem atualizar a página, o aviso aparece em até um ciclo de consulta, com a rede disponível. “Abrir ordem” mostra o lote correto e a situação atual.
- Solicitar, recusar, permitir e revogar senha; conferir vencimento e impedir reutilização. Chamadas diretas à API também precisam da autorização.
- Abrir card, consultar histórico, avançar etapa e confirmar coleta conforme o perfil. Atualizar com F5 e conferir login, filtros e detalhe aberto.
- Em celular, rolar somente a faixa de filtros; a página não deve ter rolagem horizontal. Confirmar que urgência e título permanecem legíveis.
