from datetime import datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

from backend.services.classificador_produtos import (
    CATEGORIA_OUTROS,
    ORDEM_CATEGORIAS,
    rotulo_categoria,
)
from frontend.services.task_service import APIError
from frontend.session import persist_state
from frontend.views.filtros import render_filtros
from frontend.views.paginacao import carregar_pagina, render_paginacao

FUSO = ZoneInfo("America/Bahia")
ETAPAS = {
    "PENDENTE": "Pendente",
    "CORTANDO": "Cortando",
    "COSTURANDO": "Costurando",
    "PRONTO": "Pronto",
}
PROXIMA = {
    "PENDENTE": ("CORTANDO", "Iniciar corte"),
    "CORTANDO": ("COSTURANDO", "Iniciar costura"),
    "COSTURANDO": ("PRONTO", "Marcar lote pronto"),
}


def horario(value):
    return (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        .astimezone(FUSO)
        .strftime("%d/%m/%Y %H:%M")
    )


def command(ordem, acao):
    key = f"envio_{ordem['id']}_{ordem['versao']}_{acao}"
    if key not in st.session_state:
        st.session_state[key] = str(uuid4())
    return {"request_id": st.session_state[key], "versao": ordem["versao"]}


def _categoria_ordem(ordem):
    codigo = ordem.get("categoria") or CATEGORIA_OUTROS
    return codigo if codigo in ORDEM_CATEGORIAS else CATEGORIA_OUTROS


def selecionar_ordem(ident):
    st.session_state["ordem_detalhe"] = ident


def fechar_detalhes():
    st.session_state["ordem_detalhe"] = 0


def render_ordem(service, token, user, report_error, ordem, admin, setor):
    ident = ordem["id"]
    urgente = ordem["prioridade"] == "URGENTE"
    encerrada = ordem["cancelado_em"] or ordem["coletado_em"]
    atrasada = (
        not encerrada
        and ordem["status"] != "PRONTO"
        and datetime.fromisoformat(ordem["prazo"].replace("Z", "+00:00")) < datetime.now(FUSO)
    )
    with st.container(border=True, key=f"card_{'urgente' if urgente else 'normal'}_{ident}"):
        st.markdown(":red[**URGENTE**]" if urgente else ":blue[**NORMAL**]")
        if st.button(
            f"**#{ident} — {ordem['produto']}**",
            key=f"abrir_ordem_{ident}",
            width="stretch",
            on_click=selecionar_ordem,
            args=(ident,),
            help="Abrir detalhes e ações desta ordem",
        ):
            st.rerun()
        situacao = (
            "Cancelada"
            if ordem["cancelado_em"]
            else "Coletada"
            if ordem["coletado_em"]
            else ETAPAS[ordem["status"]]
        )
        st.caption(
            f"{ordem['quantidade']} {ordem['unidade']} · {rotulo_categoria(_categoria_ordem(ordem))}"
        )
        if situacao == "Pronto":
            st.markdown(":green[**Pronto para coleta**]")
        else:
            st.markdown(f"**{situacao}**")
        st.caption(f"Prazo: {horario(ordem['prazo'])}")
        if atrasada:
            st.markdown(":orange[**Prazo vencido**]")


@st.dialog("Detalhes da ordem", width="large", on_dismiss=fechar_detalhes)
def abrir_detalhes(service, token, report_error, ident):
    token = st.session_state.get("access_token", token)
    try:
        user = service.me(token)
        ordem = service.detalhe_ordem(ident, token)
    except APIError as error:
        report_error(error)
        if st.button("Fechar detalhes", on_click=fechar_detalhes):
            st.rerun()
        return
    admin, setor = user["perfil"] == "ADMIN", user["setor"]
    encerrada = ordem["cancelado_em"] or ordem["coletado_em"]
    st.subheader(f"#{ident} — {ordem['produto']}")
    st.markdown(":red[**URGENTE**]" if ordem["prioridade"] == "URGENTE" else ":blue[**NORMAL**]")
    st.caption(f"{ordem['quantidade']} {ordem['unidade']} · Prazo: {horario(ordem['prazo'])}")
    st.text(ordem["especificacao"])
    if ordem["observacao"]:
        st.text(ordem["observacao"])
    st.caption(
        f"Solicitante: {ordem['solicitante_nome']} · Responsável: {ordem['responsavel_nome'] or 'Ainda não iniciada'}"
    )
    if ordem["cancelado_em"]:
        st.warning("Ordem cancelada.")
    elif ordem["coletado_em"]:
        st.success(f"Coletada por {ordem['coletado_nome']} em {horario(ordem['coletado_em'])}")
    elif ordem["status"] == "PRONTO":
        st.success("Produto disponível para coleta e embalagem — lote completo.")
    else:
        st.info(ETAPAS[ordem["status"]])
    if not encerrada and (admin or setor == "PRODUCAO") and ordem["status"] in PROXIMA:
        destino, label = PROXIMA[ordem["status"]]
        if st.button(label, key=f"etapa_{ident}"):
            try:
                service.etapa_ordem(ident, {**command(ordem, destino), "status": destino}, token)
                st.session_state.flash = f"Ordem #{ident}: {ETAPAS[destino]}."
                st.rerun()
            except APIError as error:
                report_error(error)
    if not encerrada and ordem["status"] == "PRONTO" and (admin or setor == "COLETA_EMBALAGEM"):
        if st.checkbox("Confirmo a retirada de todo o lote", key=f"retirada_{ident}"):
            if st.button("Confirmar coleta", key=f"coleta_{ident}"):
                try:
                    service.coletar_ordem(ident, command(ordem, "COLETA"), token)
                    st.session_state.flash = f"Coleta da ordem #{ident} registrada."
                    st.rerun()
                except APIError as error:
                    report_error(error)
    if admin and not encerrada:
        with st.expander("Cancelar ordem"):
            with st.form(f"cancelar_{ident}"):
                motivo = st.text_input("Justificativa", max_chars=500)
                if st.form_submit_button("Confirmar cancelamento"):
                    if len(motivo.strip()) < 5:
                        st.error("Informe uma justificativa com pelo menos 5 caracteres.")
                    else:
                        try:
                            service.cancelar_ordem(
                                ident,
                                {
                                    **command(ordem, "CANCELAMENTO"),
                                    "motivo": motivo.strip(),
                                },
                                token,
                            )
                            st.session_state.flash = (
                                f"Ordem #{ident} cancelada. Histórico preservado."
                            )
                            st.rerun()
                        except APIError as error:
                            report_error(error)
    if st.checkbox("Mostrar histórico", key=f"historico_{ident}"):
        try:
            eventos = service.historico_ordem(ident, token)
            for evento in eventos:
                st.text(
                    f"{horario(evento['criado_em'])} — {evento['usuario_nome']} — "
                    f"{evento['acao']} — {ETAPAS[evento['status_novo']]}"
                )
                if evento["motivo"]:
                    st.text(evento["motivo"])
        except APIError as error:
            report_error(error)

    if st.button("Fechar detalhes", on_click=fechar_detalhes):
        st.rerun()
    persist_state(service)


def render_cards(service, token, user, report_error, ordens):
    for start in range(0, len(ordens), 2):
        for col, ordem in zip(st.columns(2), ordens[start : start + 2]):
            with col:
                render_ordem(
                    service,
                    token,
                    user,
                    report_error,
                    ordem,
                    user["perfil"] == "ADMIN",
                    user["setor"],
                )


def render_ordens(service, token, user, report_error):
    st.title("Ordens de produção")
    admin = user["perfil"] == "ADMIN"
    setor = user["setor"]
    if st.session_state.pop("limpar_nova_ordem", False):
        for key in ("op_produto", "op_especificacao", "op_observacao"):
            st.session_state[key] = ""
        st.session_state["op_quantidade"] = 1
    if admin or setor == "SOLICITACAO":
        with st.expander("Nova ordem"):
            with st.container(border=True):
                st.caption("Rascunho salvo ao confirmar cada campo (Enter ou sair do campo).")
                produto = st.text_input("Produto", max_chars=150, key="op_produto")
                especificacao = st.text_input(
                    "Especificação (medida, cor ou tecido)", max_chars=500, key="op_especificacao"
                )
                quantidade = st.number_input(
                    "Quantidade do lote",
                    min_value=1,
                    max_value=1000000,
                    step=1,
                    key="op_quantidade",
                )
                unidade = st.selectbox(
                    "Unidade",
                    ["pecas", "kits"],
                    key="op_unidade",
                    format_func=lambda v: "Peças" if v == "pecas" else "Kits",
                )
                prioridade = st.selectbox(
                    "Prioridade da ordem",
                    ["NORMAL", "URGENTE"],
                    format_func=str.title,
                    key="op_prioridade",
                )
                dia = st.date_input(
                    "Data limite", value=datetime.now(FUSO).date() + timedelta(days=1), key="op_dia"
                )
                hora = st.time_input("Horário limite", value=time(17), key="op_hora")
                observacao = st.text_area("Observação", max_chars=1000, key="op_observacao")
                st.caption(
                    "Horário da Bahia. Cada ordem representa um lote completo. "
                    "A categoria é definida automaticamente."
                )
                if st.button("Enviar para produção", type="primary"):
                    if (
                        not produto.strip()
                        or not especificacao.strip()
                        or dia is None
                        or hora is None
                    ):
                        st.error("Informe produto, especificação e prazo completo.")
                    else:
                        if "nova_ordem_request" not in st.session_state:
                            st.session_state.nova_ordem_request = str(uuid4())
                        data = {
                            "request_id": st.session_state.nova_ordem_request,
                            "produto": produto.strip(),
                            "especificacao": especificacao.strip(),
                            "quantidade": quantidade,
                            "unidade": unidade,
                            "prioridade": prioridade,
                            "prazo": datetime.combine(dia, hora, tzinfo=FUSO).isoformat(),
                            "observacao": observacao.strip(),
                        }
                        try:
                            persist_state(service, required=True)
                            ordem = service.criar_ordem(data, token)
                            del st.session_state["nova_ordem_request"]
                            st.session_state.get("saved_ui", {}).pop("nova_ordem_request", None)
                            st.session_state.limpar_nova_ordem = True
                            st.session_state.flash = (
                                f"Ordem #{ordem['id']} enviada para produção "
                                f"({rotulo_categoria(_categoria_ordem(ordem))})."
                            )
                            st.rerun()
                        except APIError as error:
                            report_error(error)
    render_fila(service, token, user, report_error)


@st.fragment(run_every="10s")
def render_fila(service, token, user, report_error):
    # O temporizador não reexecuta o formulário de criação nem o diálogo aberto.
    token = st.session_state.get("access_token", token)
    try:
        _render_fila(service, token, user, report_error)
    finally:
        persist_state(service)


def _render_fila(service, token, user, report_error):
    setor = user["setor"]
    st.caption("Fila compartilhada · atualização automática a cada 10 segundos com a tela ativa.")
    st.button("Atualizar fila")
    status, situacao, categoria_filtro = render_filtros(
        "ordens",
        "ordens_pagina",
        etapa_inicial="PRONTO" if setor == "COLETA_EMBALAGEM" else "TODAS",
    )
    params = {"situacao": situacao}
    if categoria_filtro != "TODAS":
        params["categoria"] = categoria_filtro
    if status != "TODAS":
        params["status"] = status
    try:
        resultado, pagina, paginas = carregar_pagina(
            lambda **kwargs: service.pagina_ordens(token, **kwargs), "ordens_pagina", **params
        )
        ordens = resultado["itens"]
        st.caption(f"Última consulta: {datetime.now(FUSO):%H:%M:%S} (Bahia).")
    except APIError as error:
        report_error(error)
        return
    render_paginacao("ordens_pagina", pagina, paginas, resultado["total"])
    if not ordens:
        st.info("Nenhuma ordem encontrada para os filtros selecionados.")
        st.caption(
            "Até 20 ordens por página. Urgentes primeiro; em cada prioridade, menor prazo primeiro."
        )
        return
    # A API ordena globalmente por prioridade e prazo antes da paginação.
    render_cards(service, token, user, report_error, ordens)
    st.caption(
        "Até 20 ordens por página. Urgentes primeiro; em cada prioridade, menor prazo primeiro."
    )
