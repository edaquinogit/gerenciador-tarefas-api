# Administrador, funcionários e setores

## Começar

Na raiz do projeto, com ambiente virtual e `.env` configurados:

```bash
python -m alembic upgrade head
python -m backend.scripts.criar_admin --username patrao --email patrao@example.com
```

Informe e confirme uma senha (mínimo 8 caracteres, máximo 72 bytes UTF-8). Rode o bootstrap uma única vez com a API parada. Ele recusa um segundo administrador e não promove contas existentes; se usuário/e-mail já estiverem ocupados, escolha outros para o novo cadastro administrativo.

Depois inicie API e Streamlit conforme o README. O administrador entra diretamente no painel **Funcionários e setores**. Cadastre uma conta individual para cada funcionário e informe as credenciais diretamente à pessoa. O funcionário pode alterar a senha em **Minha conta**.

## Setores desta versão

| Código | Nome | Uso previsto na fase de ordens |
|---|---|---|
| `SOLICITACAO` | Solicitação | Quem solicita os produtos em cima |
| `PRODUCAO` | Produção | Corte e costura embaixo |
| `COLETA_EMBALAGEM` | Coleta e embalagem | Quem retira e embala |

Os três setores são fixos; não há cadastro livre de setores. Cada funcionário tem um setor. Contas legadas ou de desenvolvimento podem estar sem setor e aparecem destacadas para classificação. O administrador não precisa de setor.

## Permissões implementadas

| Operação | Administrador | Funcionário |
|---|---|---|
| Consultar a própria conta e alterar sua senha | Sim | Sim |
| Consultar catálogo de setores | Sim | Sim |
| Cadastrar/listar funcionários | Sim | Não |
| Definir setor e ativação de funcionário | Sim | Não |
| Redefinir senha de funcionário | Sim | Não |
| Gerenciar tarefas pessoais | Próprias | Próprias |
| Promover conta a administrador pela API | Não | Não |

A proteção existe no backend, mesmo se alguém chamar a API diretamente. A interface consulta `/usuarios/me` em cada execução; não usa o nome da conta para conceder acesso.

O painel gerencia apenas funcionários. A conta administrativa não pode ser desativada ou alterada pelos endpoints de funcionários, evitando remover o único acesso de gestão. O administrador pode trocar a própria senha usando a senha atual. Recuperação de senha esquecida do administrador exige manutenção local; não há recuperação por e-mail nesta versão.

Salvar setor/ativação e redefinir senha revogam todas as sessões anteriores do funcionário. Reativar exige novo login. Trocar a própria senha também encerra as sessões anteriores. Nenhuma dessas ações exclui tarefas.

O cadastro público permanece desabilitado por padrão. `ALLOW_REGISTRATION=true` é uma opção de desenvolvimento e cria somente funcionários sem setor; não permite enviar perfil ou privilégios. Para o uso da empresa mantenha `false`.

Para manutenção local, há também cadastro de funcionário por terminal:

```bash
python -m backend.scripts.criar_usuario --username operador --email operador@example.com --setor PRODUCAO
```

## Limite desta entrega

As telas ainda trabalham com tarefas pessoais. O setor já está cadastrado e visível, mas não transforma tarefas em uma fila compartilhada. A próxima fase adicionará ordens e autorizará solicitação, corte/costura e coleta conforme o setor.
