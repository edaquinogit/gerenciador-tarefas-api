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


def agrupar_por_categoria(ordens):
    grupos = {codigo: [] for codigo in ORDEM_CATEGORIAS}
    for ordem in ordens:
        grupos[_categoria_ordem(ordem)].append(ordem)
    return [(codigo, itens) for codigo, itens in grupos.items() if itens]


def render_ordem(service, token, user, report_error, ordem, admin, setor):
    ident = ordem["id"]
    encerrada = ordem["cancelado_em"] or ordem["coletado_em"]
    with st.container(border=True):
        st.markdown(f"**#{ident} — {ordem['produto']}**")
        st.caption(
            f"{rotulo_categoria(_categoria_ordem(ordem))} • "
            f"{ordem['quantidade']} {ordem['unidade']} • "
            f"{ETAPAS[ordem['status']]} • "
            f"Prazo: {horario(ordem['prazo'])}"
        )
        if ordem["prioridade"] == "URGENTE":
            st.warning("Prioridade: URGENTE")
        else:
            st.caption("Prioridade: Normal")
        if ordem["cancelado_em"]:
            st.warning(f"Cancelada em {horario(ordem['cancelado_em'])}")
        elif ordem["coletado_em"]:
            st.success(f"Coletada por {ordem['coletado_nome']} em {horario(ordem['coletado_em'])}")
        elif ordem["status"] == "PRONTO":
            st.success("Produto disponível para coleta e embalagem — lote completo.")
        else:
            st.info(ETAPAS[ordem["status"]])
        with st.expander("Detalhes"):
            st.text(ordem["especificacao"])
            if ordem["observacao"]:
                st.text(ordem["observacao"])
            st.caption(
                f"Solicitante: {ordem['solicitante_nome']} • "
                f"Responsável pela última etapa: "
                f"{ordem['responsavel_nome'] or 'Ainda não iniciada'}"
            )
        if not encerrada and (admin or setor == "PRODUCAO") and ordem["status"] in PROXIMA:
            destino, label = PROXIMA[ordem["status"]]
            if st.button(label, key=f"etapa_{ident}"):
                try:
                    service.etapa_ordem(
                        ident, {**command(ordem, destino), "status": destino}, token
                    )
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


def reset_pagina_ordens():
    st.session_state["ordens_pagina"] = 1


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
    st.caption("Fila compartilhada entre os setores. Use Atualizar fila para consultar mudanças.")
    st.button("Atualizar fila")
    filtros = st.columns(3)
    status = filtros[0].selectbox(
        "Etapa",
        ["TODAS", *ETAPAS],
        key="ordens_etapa",
        index=4 if setor == "COLETA_EMBALAGEM" else 0,
        format_func=lambda v: ETAPAS.get(v, "Todas"),
        on_change=reset_pagina_ordens,
    )
    situacao = filtros[1].selectbox(
        "Situação",
        ["ativas", "coletadas", "canceladas", "todas"],
        key="ordens_situacao",
        format_func=str.title,
        on_change=reset_pagina_ordens,
    )
    categoria_filtro = filtros[2].selectbox(
        "Categoria",
        ["TODAS", *ORDEM_CATEGORIAS],
        key="ordens_categoria",
        format_func=lambda v: "Todas" if v == "TODAS" else rotulo_categoria(v),
        on_change=reset_pagina_ordens,
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
    except APIError as error:
        report_error(error)
        return
    render_paginacao("ordens_pagina", pagina, paginas, resultado["total"])
    if not ordens:
        st.info("Nenhuma ordem encontrada para os filtros selecionados.")
        st.caption(
            "Até 20 ordens por página. Urgentes no topo, em ordem de prazo; demais ordens por categoria. Contagens dos grupos referem-se apenas a esta página."
        )
        return
    urgentes = [ordem for ordem in ordens if ordem["prioridade"] == "URGENTE"]
    if urgentes:
        st.subheader(f"Urgentes — {len(urgentes)} nesta página")
        for ordem in urgentes:
            render_ordem(service, token, user, report_error, ordem, admin, setor)
    normais = [ordem for ordem in ordens if ordem["prioridade"] != "URGENTE"]
    for codigo, itens in agrupar_por_categoria(normais):
        quantidade = len(itens)
        rotulo = rotulo_categoria(codigo)
        titulo = f"{rotulo} — {quantidade} {'ordem' if quantidade == 1 else 'ordens'}"
        st.subheader(titulo)
        for ordem in itens:
            render_ordem(service, token, user, report_error, ordem, admin, setor)
    st.caption(
        "Até 20 ordens por página. Urgentes no topo, em ordem de prazo; demais ordens por categoria. Contagens dos grupos referem-se apenas a esta página."
    )
