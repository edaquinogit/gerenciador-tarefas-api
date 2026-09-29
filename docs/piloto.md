# Teste prático entre setores

Objetivo: ensaiar um lote fictício completo com uma pessoa na solicitação, uma na produção, uma na coleta/embalagem e o administrador acompanhando. Reserve 30–45 minutos. Este ensaio não substitui o controle atual da fábrica.

## Preparação no computador que hospedará o teste

Use Python 3.11 ou 3.12, preferencialmente Windows nativo se os outros computadores forem Windows. A branch `main` reúne as etapas de base, acessos, ordens, avisos, ensaio e painel administrativo. Em um clone do projeto, sem alterações locais pendentes:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
python -m venv .venv
```

Ative o ambiente: PowerShell `.venv\Scripts\Activate.ps1`, CMD `.venv\Scripts\activate.bat` ou Linux/macOS `source .venv/bin/activate`. Se o PowerShell bloquear a ativação, use o CMD; não é necessário mudar políticas do computador.

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
python -m backend.scripts.piloto preparar
python -m backend.scripts.piloto iniciar
```

Abra http://localhost:8502. A faixa **AMBIENTE DE TESTE** deve aparecer inclusive na tela de login. Não é necessário criar ou editar `.env`: o comando define explicitamente o banco, a chave e a API deste ensaio.

A pasta `.pilot` contém banco SQLite, configuração e `acessos.json` com quatro senhas aleatórias. Abra esse arquivo localmente e entregue a cada participante somente seu próprio acesso; não publique o arquivo no GitHub, em capturas ou no grupo. No Windows, mantenha a pasta sob seu usuário, com acesso restrito. Não existem senhas padrão no código.

| Conta | Papel no teste |
|---|---|
| `piloto_admin` | Administrador, acompanha tudo e gerencia funcionários |
| `piloto_solicitacao` | Abre a ordem e recebe o aviso de pronto |
| `piloto_producao` | Avança corte, costura e pronto |
| `piloto_coleta` | Recebe o aviso e confirma a coleta do lote |

Use computadores, perfis de navegador ou sessões independentes. Quatro abas compartilhando uma sessão não são uma boa simulação de quatro funcionários. Para testar com mais pessoas, o administrador deve cadastrar uma conta por pessoa.

Os contatos das contas de demonstração são números fictícios usados somente para validar o formulário; o sistema não envia mensagens ou ligações. Para atualizar um ensaio antigo, preserve/mova a pasta `.pilot` inteira e prepare um novo ensaio com a versão atual.

## Compartilhar com os setores

Pare o comando anterior com Ctrl+C e inicie:

```bash
python -m backend.scripts.piloto iniciar --rede
```

No Windows, use `ipconfig` para consultar o IPv4 do computador anfitrião. Os demais abrem `http://IP-DO-ANFITRIAO:8502`, por exemplo `http://192.168.1.20:8502`. Todos precisam estar na mesma rede local confiável. Se necessário, peça ao responsável pela rede liberação da porta TCP 8502 apenas na rede privada. Não abra portas no roteador nem publique este ensaio na internet: ele usa HTTP e dados fictícios.

A API permanece em `127.0.0.1:8001`; os setores não precisam acessá-la diretamente. Apenas um computador executa o sistema e guarda o banco. Não coloque SQLite em pasta compartilhada de rede. Mantenha o anfitrião ligado, sem suspensão. No WSL, o acesso pela LAN depende da configuração de rede do Windows/WSL e não foi validado; prefira Python nativo para este roteiro.

## Roteiro de aceite

Anote o ID da ordem e os horários. Na fila, use **Atualizar** após cada mudança de outro setor. Os avisos consultam novidades a cada 10 segundos enquanto a sessão está ativa; se a aba ficar suspensa pelo navegador, retome-a e atualize. Ler um aviso não confirma a coleta.

| Passo | Responsável / ação | Resultado esperado |
|---|---|---|
| 1 | Cada participante entra com sua conta | Papel e setor corretos; funcionário sem gestão de contas |
| 2 | Solicitação cria “TESTE – lote 01”, 10 peças, especificação fictícia e prazo futuro | Uma ordem PENDENTE com ID e solicitante |
| 3 | Produção atualiza a fila | Mesma ordem, quantidade e especificação |
| 4 | Produção marca CORTANDO e depois COSTURANDO | Histórico registra autor, etapa e horário; ainda sem aviso de pronto |
| 5 | Produção marca PRONTO | Admin, solicitante e coleta recebem um aviso cada, disponível para coleta |
| 6 | Solicitação marca seu aviso como lido | Aviso da coleta continua não lido; ordem continua aguardando coleta |
| 7 | Coleta confirma o lote completo | Ordem registra coletor e horário; aviso passa a indicar coletada |
| 8 | Admin clica em Todas as tarefas no topo, acompanha uma mudança e abre o histórico em Ordens de produção | Painel atualiza em até o próximo ciclo de consulta com a aba ativa; histórico mantém a sequência completa |
| 9 | Todos saem; anfitrião encerra e inicia novamente | Novo login mantém ordem, histórico, avisos e leituras |

A embalagem física faz parte da rotina do setor, mas **não há status “EMBALADO”**: a confirmação registra coleta. Também não há entrega parcial, reabertura ou edição de ordem.

Faça ainda dois ensaios curtos:

- **Disputa:** duas sessões da produção abrem a mesma versão de uma segunda ordem; ambas tentam avançar. A segunda deve receber conflito/solicitação de atualização; o histórico registra uma única mudança. Atualize antes de continuar.
- **Cancelamento e acesso:** o admin cancela uma terceira ordem pronta com justificativa; após atualização, a coleta não pode confirmá-la e o aviso indica cancelada. O admin desativa um funcionário de teste; o próximo acesso autenticado desse funcionário deve ser recusado. Reative ao terminar.

## Registro do resultado

Copie e preencha, sem senhas:

- Data, versão/commit e anfitrião:
- Participantes por setor:
- IDs das três ordens:
- Passos aprovados / reprovados:
- Hora de PRONTO / hora do aviso em cada tela:
- Falha encontrada, ação, resultado esperado e observado:
- Captura sem dados pessoais ou credenciais:
- Decisão do responsável: repetir ensaio / aprovado para próxima etapa:

Considere aprovado quando todos os passos funcionarem, sem ordens ou avisos duplicados, sem avanço por setor incorreto e com dados preservados após reiniciar. Se houver falha, mantenha o controle atual da fábrica, registre o problema e interrompa o ensaio quando houver risco de confusão na coleta. O tempo observado aqui não é garantia de capacidade em produção.

## Encerrar, retomar e resolver problemas

Ctrl+C encerra os dois processos e preserva os dados. Para retomar, execute somente `iniciar` (ou `iniciar --rede`), usando a mesma pasta e versão do código. `preparar` recusa uma `.pilot` existente, inclusive incompleta. Para um novo ensaio, com os serviços parados, mova a pasta inteira para fora do repositório e guarde-a com acesso restrito; depois execute `preparar`. Não apague o banco da empresa.

- **Porta ocupada:** encerre a instância anterior; não mate processos desconhecidos. O iniciador recusa portas 8001/8502 ocupadas.
- **Preparação interrompida:** não reutilize pasta parcial; preserve/mova a pasta e repita após corrigir a dependência ou permissão apontada no terminal.
- **Migração pendente ou banco incompatível:** o início verifica o schema e recusa continuar. Preserve a pasta e peça revisão; não aplique migrações no banco real para resolver o ensaio.
- **Senha esquecida:** admin pode redefinir a senha do funcionário; `acessos.json` contém apenas as senhas iniciais. Se esquecer a senha administrativa, prepare um novo ensaio preservando o anterior.
- **Sessão expirada:** entre novamente; os tokens duram 60 minutos.
- **Aviso não aparece:** mantenha aba ativa, atualize, confira destinatário/setor e se a etapa realmente ficou PRONTO. Avisos vão ao solicitante, administradores ativos e funcionários ativos de coleta existentes naquele momento.
- **“Coletada” some da fila:** selecione a situação correspondente; ordens encerradas não aparecem no filtro de ativas.

Antes de usar dados reais, ainda são necessárias validação presencial da rede e dos dispositivos, política de backup com restauração testada, hospedagem protegida, definição de responsáveis e avaliação de concorrência/capacidade. Nenhuma implantação na empresa foi realizada por este PR.
