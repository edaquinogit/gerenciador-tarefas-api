# Sessões, navegação e experiência de uso — 2.6

## O que muda

- F5 recupera o login, a tela, os filtros e a página enquanto a sessão for válida.
- A sessão dura no máximo 12 horas, configurável entre 1 e 24 (`SESSION_HOURS`). A renovação do JWT não estende esse limite. A interface avisa nos últimos 15 minutos.
- Sair revoga a sessão no servidor e apaga o cookie; trocar senha, desativar ou alterar o setor invalida acessos anteriores. Falha de rede no logout mostra erro para tentar novamente.
- O cookie é HttpOnly, SameSite=Strict, limitado a `/sessoes`; o banco armazena somente hashes do segredo e do código de vinculação. JavaScript não lê o cookie. Não há token em URL ou localStorage.
- A interface obtém um código de uso único após login. O navegador o troca pelo cookie em uma origem autorizada; a API valida origem e cabeçalho contra CSRF. O token curto fica em memória e é renovado pelo cookie.
- Rascunho da nova ordem e navegação são salvos por sessão no servidor. Campos de texto são confirmados com Enter ou ao sair do campo. Texto ainda não confirmado não é recuperável após fechar a aba. Senhas e formulários de administração/conta não são persistidos.
- Trocar de tela preserva filtros e rascunho. Sair ou chegar ao fim da sessão encerra essa recuperação. Abas do mesmo navegador compartilham o cookie; prefira uma aba de edição por conta. Navegadores/perfis diferentes têm sessões independentes.
- Avisos usam a mesma navegação Anterior/Próxima das ordens e do painel, com total filtrado, limites e correção quando a última página esvazia.
- Tema único com contraste, área de trabalho ampla, identificação do perfil/setor, filtros alinhados e login centralizado. Avisos permanecem disponíveis em seção recolhível, sem deslocar a fila a cada atualização.

## Atualizar no Windows / VS Code

Pare API e Streamlit com Ctrl+C. Não apague `.env`, banco, funcionários ou ordens. Na raiz do projeto, com a venv ativada:

```bat
git switch main
git pull --ff-only origin main
python -m pip install -r requirements-dev.txt
python -m backend.scripts.backup_sqlite
python -m alembic upgrade head
python -m alembic check
```

Só prossiga para a migração se o backup terminar com sucesso. A revisão atual esperada é **0008**. A 0007 cria `sessao`; a 0008 acrescenta autorização de senha e recupera avisos ausentes. Ambas preservam as tabelas operacionais. Tokens da versão anterior precisam de novo login. Não há downgrade destrutivo: em rollback, pare os serviços e restaure um backup validado junto da versão correspondente do código.

Terminal 1:

```bat
python -m uvicorn backend.main:create_app --factory --reload
```

Terminal 2, na mesma pasta e com a venv ativada:

```bat
python -m streamlit run frontend/app.py
```

Abra http://127.0.0.1:8501. `localhost:8501` também funciona com a configuração padrão. Não alterne nomes de host durante a sessão.

## Configuração da rede

`API_URL` é o endereço que o servidor Streamlit usa. `PUBLIC_API_URL` é o endereço da API acessível pelo navegador. Se não informado, o navegador usa seu próprio protocolo/host com porta 8000. `BROWSER_ORIGINS` permite por padrão apenas `http://localhost:8501` e `http://127.0.0.1:8501`.

No ensaio em LAN, configure o IP real do servidor e a origem exata da interface em `BROWSER_ORIGINS`. Navegador e API devem usar o mesmo host/site e protocolo por causa do cookie Strict. Exemplo de `.env` em uma rede isolada de teste:

```dotenv
API_URL=http://127.0.0.1:8000
PUBLIC_API_URL=http://192.168.1.50:8000
BROWSER_ORIGINS=["http://192.168.1.50:8501"]
SESSION_COOKIE_SECURE=false
SESSION_HOURS=12
```

Substitua pelo IP do servidor; abra os serviços na interface da rede e libere somente as portas necessárias nessa rede. Em operação real, use HTTPS e `SESSION_COOKIE_SECURE=true`, sem curingas de origem. Interface HTTPS não pode chamar API HTTP. Não coloque chaves ou senhas em `PUBLIC_API_URL`. Um deploy em domínios sem relação exige uma configuração de proxy de mesmo site; não é suportado simplesmente adicionando CORS.

## Critérios de aceite

1. Entrar, selecionar Ordens de produção e um filtro, preencher um rascunho e confirmar os campos.
2. Atualizar com F5: login, tela, filtro e rascunho devem permanecer. Depois enviar: só uma ordem deve existir.
3. Trocar de tela e voltar: filtros e rascunho continuam disponíveis.
4. Com 11 avisos não lidos, abrir a página 2 e marcar o último como lido: deve voltar à página 1; Incluir avisos lidos reinicia a navegação.
5. Sair e atualizar: continua na tela de login; o token anterior deve receber 401.
6. Trocar senha/desativar conta em outro acesso: sessão antiga não pode executar operações nem se renovar.
7. Simular API indisponível: mostrar erro e preservar dados ainda em memória, sem afirmar que a operação foi concluída.

AppTest cobre a interface Python, mas não executa JavaScript. A CI também executa `tests_browser` com Chrome para validar o cookie, F5, rascunho, logout e largura reduzida, guardando capturas e logs em `browser-evidence`. Testes automatizados não substituem o ensaio nos aparelhos e na rede da empresa.

A renovação periódica do token é isolada em um fragmento: ela não redesenha os campos ainda em edição. Os painéis, avisos e detalhes utilizam o token atualizado. Entrada, saída, recuperação ou mudança de usuário continuam reconstruindo a tela quando necessário.
