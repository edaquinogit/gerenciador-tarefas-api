# Categorias de ordens

Novas ordens são classificadas no servidor em Roupa de cama, Banho, Cozinha, Cortinas, Almofadas ou Outros. O nome do produto tem prioridade; especificação e observação são consultadas apenas se o campo anterior não identificar categoria. A classificação é determinística por palavras-chave, sem IA e sem edição manual nesta versão.

Aceita acentos, maiúsculas, hífen e variações previstas como lençóis, cobre-leito e cobreleito. Toalha de mesa fica em Cozinha. Palavras são reconhecidas inteiras, evitando classificar “composição” por conter “piso”. Em um mesmo campo com múltiplas categorias, a ordem de prioridade é Roupa de cama, Banho, Cozinha, Cortinas e Almofadas; a expressão específica “toalha de mesa” tem precedência. Kits mistos precisam de conferência humana e nomes claros. Capa de sofá ainda fica em Outros.

Pedidos de cobre-leito abertos pela manhã e à tarde entram no grupo Roupa de cama, mas **não são unidos**: cada ordem mantém quantidade, responsável, prazo, status, histórico e aviso próprios. O agrupamento é por categoria, não por produto idêntico ou dia.

A tela de produção agrupa as ordens da página atual. Os títulos mostram quantas ordens existem naquela página, não o total de toda a fábrica. São até 20 ordens por página. Todas as urgentes carregadas aparecem primeiro em uma seção única, por prazo, independentemente da categoria. As demais ordens são agrupadas por categoria. A navegação usa Anterior/Próxima, informa total e número de páginas e ajusta páginas que deixarem de existir. O filtro por categoria é aplicado no banco antes da paginação e volta à página 1 quando alterado. O painel Todas as tarefas também oferece filtro e coluna de categoria para ordens.

## Atualização 0006

Pare API e Streamlit. Na instalação com `.env` e banco existentes, execute:

```bash
python -m backend.scripts.backup_sqlite
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

Prossiga com migração somente se o backup concluir. O comando utiliza o SQLite definido em DATABASE_URL, inclusive caminho absoluto, e grava cópia consistente e exclusiva em `backups/*.bak`. Não sobrescreve backups nem cria banco de origem se estiver ausente. Os arquivos não são versionados. Guarde uma cópia também em local separado do computador para proteção contra perda do dispositivo.

Resultado esperado: `0006 (head)`. Ordens antigas recebem **Outros**; não há reclassificação retroativa. A migração preserva usuários, tarefas, ordens, eventos e notificações. Downgrade destrutivo é recusado; para reverter, preserve os dados novos e restaure o backup com o código correspondente, reconciliando registros posteriores.

## Rodar no VS Code (Windows / CMD)

Abra `C:\Users\ednal\Projetos\Gerenciador_API_V3` no VS Code, fora do OneDrive. Em Terminal → Novo Terminal, selecione **Command Prompt (CMD)**. Com serviços parados e alterações locais salvas:

```cmd
cd /d "%USERPROFILE%\Projetos\Gerenciador_API_V3"
git switch main
git pull --ff-only origin main
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
```

Se já há `.env` e banco funcionando nessa pasta, use o procedimento de backup/migração acima. Não copie novamente um banco antigo por cima do atual.

Se esta cópia ainda não tem configuração/banco, escolha um dos caminhos:

- **Retomar seus cadastros:** preserve a instalação antiga, localize o banco definido no `.env` antigo e transfira-o com os serviços parados, conferindo DATABASE_URL na pasta nova. Não crie outro administrador. Não publique o conteúdo do `.env`.
- **Somente demonstração:** execute `python -m backend.scripts.piloto preparar` e depois `python -m backend.scripts.piloto iniciar`. Abra http://localhost:8502; as credenciais aleatórias ficam em `.pilot/acessos.json`. O preparador recusa uma pasta de ensaio existente. Não utiliza o banco real nem exige `.env`.

Para iniciar a instalação existente, depois do backup e da migração:

Terminal 1 (ambiente virtual ativado):

```cmd
python -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

Terminal 2:

```cmd
cd /d "%USERPROFILE%\Projetos\Gerenciador_API_V3"
.venv\Scripts\activate.bat
python -m streamlit run frontend/app.py
```

Abra http://localhost:8501. O login existente permanece. Para conferir a nova organização, crie duas ordens fictícias de cobre-leito e uma de toalha de banho e teste o filtro Categoria; confirme que as duas ordens de cama mantêm IDs e etapas independentes.
