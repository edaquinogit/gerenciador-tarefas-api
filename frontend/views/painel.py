from datetime import datetime

import streamlit as st

from backend.services.classificador_produtos import ORDEM_CATEGORIAS, rotulo_categoria
from frontend.services.task_service import APIError
from frontend.session import persist_state
from frontend.views.ordens import ETAPAS, FUSO, horario
from frontend.views.paginacao import carregar_pagina, render_paginacao, reset_page

SETORES = {
    "SOLICITACAO": "Solicitação",
    "PRODUCAO": "Produção",
    "COLETA_EMBALAGEM": "Coleta e embalagem",
}


@st.fragment(run_every="10s")
def render_painel(service, token, report_error):
    st.title("Todas as tarefas")
    st.caption(
        "Visão do administrador • atualização automática a cada 10 segundos com a tela ativa."
    )
    st.button("Atualizar agora", key="painel_atualizar")
    orders_tab, tasks_tab = st.tabs(["Ordens entre setores", "Tarefas pessoais"])
    with orders_tab:
        filtros = st.columns(3)
        etapa = filtros[0].selectbox(
            "Etapa da produção",
            ["TODAS", *ETAPAS],
            format_func=lambda v: ETAPAS.get(v, "Todas"),
            key="painel_etapa",
            on_change=reset_page,
            args=("painel_ordens_pagina",),
        )
        situacao = filtros[1].selectbox(
            "Situação das ordens",
            ["todas", "ativas", "coletadas", "canceladas"],
            format_func=lambda v: {
                "todas": "Todas",
                "ativas": "Ativas",
                "coletadas": "Coletadas",
                "canceladas": "Canceladas",
            }[v],
            key="painel_situacao",
            on_change=reset_page,
            args=("painel_ordens_pagina",),
        )
        categoria = filtros[2].selectbox(
            "Categoria das ordens",
            ["TODAS", *ORDEM_CATEGORIAS],
            format_func=lambda v: "Todas" if v == "TODAS" else rotulo_categoria(v),
            key="painel_categoria",
            on_change=reset_page,
            args=("painel_ordens_pagina",),
        )
        params = {"situacao": situacao}
        if categoria != "TODAS":
            params["categoria"] = categoria
        if etapa != "TODAS":
            params["status"] = etapa
        try:
            result, page, pages = carregar_pagina(
                lambda **kwargs: service.pagina_ordens(token, **kwargs),
                "painel_ordens_pagina",
                **params,
            )
            orders = result["itens"]
            render_paginacao("painel_ordens_pagina", page, pages, result["total"])
            if orders:
                st.dataframe(
                    [
                        {
                            "Ordem": order["id"],
                            "Produto": order["produto"],
                            "Categoria": rotulo_categoria(order["categoria"]),
                            "Quantidade": order["quantidade"],
                            "Unidade": order["unidade"],
                            "Etapa": ETAPAS[order["status"]],
                            "Situação": "Cancelada"
                            if order["cancelado_em"]
                            else "Coletada"
                            if order["coletado_em"]
                            else "Aguardando coleta"
                            if order["status"] == "PRONTO"
                            else "Em produção",
                            "Solicitante": order["solicitante_nome"],
                            "Responsável": order["responsavel_nome"] or "Não atribuído",
                            "Prioridade": order["prioridade"],
                            "Prazo": horario(order["prazo"]),
                            "Atualizada em": horario(order["atualizado_em"]),
                        }
                        for order in orders
                    ],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("Nenhuma ordem encontrada para os filtros selecionados.")
            st.caption(f"Ordens consultadas às {datetime.now(FUSO):%H:%M:%S} (Bahia).")
        except APIError as error:
            report_error(error)
    with tasks_tab:
        estado = st.selectbox(
            "Situação das tarefas",
            ["Todas", "Pendentes", "Concluídas"],
            key="painel_tarefas_estado",
            on_change=reset_page,
            args=("painel_tarefas_pagina",),
        )
        params = {}
        if estado != "Todas":
            params["concluido"] = estado == "Concluídas"
        try:
            result, page, pages = carregar_pagina(
                lambda **kwargs: service.todas_tarefas(token, **kwargs),
                "painel_tarefas_pagina",
                **params,
            )
            render_paginacao("painel_tarefas_pagina", page, pages, result["total"])
            if result["itens"]:
                st.dataframe(
                    [
                        {
                            "ID": task["id"],
                            "Tarefa": task["titulo"],
                            "Pessoa": task["usuario_nome"],
                            "Setor": SETORES.get(task["setor"], "Sem setor / administração"),
                            "Prioridade": task["prioridade"],
                            "Situação": "Concluída" if task["concluido"] else "Pendente",
                        }
                        for task in result["itens"]
                    ],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("Nenhuma tarefa encontrada para os filtros selecionados.")
            st.caption(f"Tarefas consultadas às {datetime.now(FUSO):%H:%M:%S} (Bahia).")
        except APIError as error:
            report_error(error)
    st.caption(
        "Para atuar em uma ordem, abra Ordens de produção no menu. Tarefas pessoais são alteradas pelo próprio responsável."
    )

    persist_state(service)
