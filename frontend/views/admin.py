import streamlit as st

from frontend.services.task_service import APIError
from frontend.views.ordens import horario
from shared.telefone import normalizar_telefone


def render_admin(service, token, report_error):
    st.title("Funcionários e setores")
    render_autorizacoes(service, token, report_error)
    try:
        setores = service.setores(token)
        funcionarios = service.funcionarios(token)
    except APIError as error:
        report_error(error)
        return
    nomes = {s["id"]: s["nome"] for s in setores}
    ativos = [f for f in funcionarios if f["is_active"]]
    st.caption(f"{len(ativos)} funcionários ativos • {len(funcionarios) - len(ativos)} inativos")
    cols = st.columns(len(setores))
    for col, setor in zip(cols, setores, strict=True):
        col.metric(setor["nome"], sum(f["setor"] == setor["id"] for f in ativos))
    sem_setor = sum(f["setor"] is None for f in ativos)
    if sem_setor:
        st.warning(f"{sem_setor} funcionário(s) ativo(s) aguardando definição de setor.")

    with st.expander("Cadastrar funcionário"):
        with st.form("cadastro_funcionario", clear_on_submit=True):
            username = st.text_input("Nome de usuário", max_chars=64)
            telefone = st.text_input(
                "Telefone com DDD", max_chars=32, placeholder="(79) 99999-0000"
            )
            setor = st.selectbox("Setor", list(nomes), format_func=nomes.get)
            password = st.text_input("Senha inicial", type="password")
            confirm = st.text_input("Confirme a senha inicial", type="password")
            if st.form_submit_button("Cadastrar"):
                if password != confirm:
                    st.error("As senhas não coincidem.")
                elif (
                    not username.strip()
                    or not telefone.strip()
                    or len(password) < 8
                    or len(password.encode()) > 72
                ):
                    st.error(
                        "Preencha usuário, telefone com DDD e senha com mínimo de 8 caracteres e máximo de 72 bytes."
                    )
                else:
                    try:
                        service.criar_funcionario(
                            {
                                "username": username.strip(),
                                "telefone": normalizar_telefone(telefone),
                                "setor": setor,
                                "password": password,
                            },
                            token,
                        )
                        st.session_state.flash = (
                            "Funcionário cadastrado. Informe as credenciais diretamente à pessoa."
                        )
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
                    except APIError as error:
                        report_error(error)

    filtro = st.selectbox(
        "Filtrar por setor",
        ["TODOS", "SEM_SETOR", *nomes],
        format_func=lambda v: {"TODOS": "Todos", "SEM_SETOR": "Sem setor"}.get(v, nomes.get(v)),
    )
    filtrados = [
        f
        for f in funcionarios
        if filtro == "TODOS"
        or (filtro == "SEM_SETOR" and f["setor"] is None)
        or f["setor"] == filtro
    ]
    if not filtrados:
        st.info("Nenhum funcionário neste filtro.")
    for funcionario in filtrados:
        ident = funcionario["id"]
        with st.expander(
            f"{funcionario['username']} — {nomes.get(funcionario['setor'], 'Sem setor')} — {'Ativo' if funcionario['is_active'] else 'Inativo'}"
        ):
            st.text(f"Telefone: {funcionario['telefone'] or 'Não informado'}")
            with st.form(f"editar_{ident}"):
                telefone_atual = st.text_input(
                    "Telefone do funcionário",
                    value=funcionario["telefone"] or "",
                    max_chars=32,
                    key=f"telefone_{ident}",
                )
                options = list(nomes)
                setor = st.selectbox(
                    "Setor do funcionário",
                    options,
                    index=options.index(funcionario["setor"])
                    if funcionario["setor"] in options
                    else None,
                    placeholder="Selecione um setor",
                    format_func=nomes.get,
                )
                ativo = st.checkbox("Conta ativa", value=funcionario["is_active"])
                st.caption(
                    "Salvar encerra as sessões desse funcionário. Desativar preserva suas tarefas."
                )
                if st.form_submit_button("Salvar alterações"):
                    if setor is None:
                        st.error("Selecione um setor.")
                    else:
                        try:
                            data = {"setor": setor, "is_active": ativo}
                            if telefone_atual.strip() or funcionario["telefone"]:
                                data["telefone"] = normalizar_telefone(telefone_atual)
                            service.atualizar_funcionario(ident, data, token)
                            st.session_state.flash = (
                                "Funcionário atualizado. Será necessário entrar novamente."
                            )
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                        except APIError as error:
                            report_error(error)

            with st.form(f"senha_{ident}", clear_on_submit=True):
                password = st.text_input("Nova senha", type="password")
                confirm = st.text_input("Confirme a nova senha", type="password")
                if st.form_submit_button("Redefinir senha"):
                    if password != confirm or len(password) < 8 or len(password.encode()) > 72:
                        st.error(
                            "Confirme uma senha com mínimo de 8 caracteres e máximo de 72 bytes."
                        )
                    else:
                        try:
                            service.redefinir_senha(ident, password, token)
                            st.session_state.flash = (
                                "Senha redefinida e sessões anteriores encerradas."
                            )
                            st.rerun()
                        except APIError as error:
                            report_error(error)


@st.fragment(run_every="10s")
def render_autorizacoes(service, token, report_error):
    try:
        pedidos = service.autorizacoes_senha(token)
    except APIError as error:
        report_error(error)
        return
    pendentes = [p for p in pedidos if p["status"] in {"PENDENTE", "AUTORIZADA"}]
    with st.expander(
        f"Autorizações de senha · {len(pendentes)} em aberto", expanded=bool(pendentes)
    ):
        st.caption("Cada liberação vale por 30 minutos e permite uma única troca de senha.")
        if not pendentes:
            st.caption("Nenhuma solicitação em aberto.")
        for pedido in pendentes:
            ident = pedido["usuario_id"]
            st.text(f"{pedido['username']} · {pedido['status'].title()}")
            if pedido["status"] == "AUTORIZADA":
                st.caption(f"Válida até {horario(pedido['expira_em'])}")
            cols = st.columns(2)
            acao = None
            if pedido["status"] == "PENDENTE" and cols[0].button(
                "Permitir troca", key=f"permitir_senha_{ident}"
            ):
                acao = True
            if cols[1].button(
                "Revogar" if pedido["status"] == "AUTORIZADA" else "Recusar",
                key=f"recusar_senha_{ident}",
            ):
                acao = False
            if acao is not None:
                try:
                    service.decidir_senha(ident, acao, pedido["versao"], token)
                    st.rerun()
                except APIError as error:
                    report_error(error)
