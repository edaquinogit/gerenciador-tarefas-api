from datetime import datetime

import streamlit as st

from frontend.services.task_service import APIError
from frontend.views.ordens import ETAPAS, FUSO, horario

SETORES = {
    "SOLICITACAO": "Solicitação",
    "PRODUCAO": "Produção",
    "COLETA_EMBALAGEM": "Coleta e embalagem",
}


def reset_page(key):
    st.session_state[key] = 1


@st.fragment(run_every="10s")
def render_painel(service, token, report_error):
    st.title("Todas as tarefas")
    st.caption(
        "Visão do administrador • atualização automática a cada 10 segundos com a tela ativa."
    )
    st.button("Atualizar agora", key="painel_atualizar")
    orders_tab, tasks_tab = st.tabs(["Ordens entre setores", "Tarefas pessoais"])
    with orders_tab:
        etapa = st.selectbox(
            "Etapa da produção",
            ["TODAS", *ETAPAS],
            format_func=lambda v: ETAPAS.get(v, "Todas"),
            key="painel_etapa",
            on_change=reset_page,
            args=("painel_ordens_pagina",),
        )
        situacao = st.selectbox(
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
        page = int(
            st.number_input("Página de ordens", min_value=1, step=1, key="painel_ordens_pagina")
        )
        params = {"situacao": situacao, "offset": (page - 1) * 20, "limit": 21}
        if etapa != "TODAS":
            params["status"] = etapa
        try:
            orders = service.ordens(token, **params)
            if orders:
                st.dataframe(
                    [
                        {
                            "Ordem": order["id"],
                            "Produto": order["produto"],
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
                        for order in orders[:20]
                    ],
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "Há mais ordens na próxima página."
                    if len(orders) > 20
                    else "Última página deste filtro."
                )
            else:
                st.info("Nenhuma ordem nesta página. Confira os filtros e o número da página.")
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
        page = int(
            st.number_input("Página de tarefas", min_value=1, step=1, key="painel_tarefas_pagina")
        )
        params = {"offset": (page - 1) * 20, "limit": 20}
        if estado != "Todas":
            params["concluido"] = estado == "Concluídas"
        try:
            result = service.todas_tarefas(token, **params)
            st.caption(f"{result['total']} tarefa(s) no filtro • página {page}.")
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
                st.info("Nenhuma tarefa nesta página. Confira os filtros e o número da página.")
            st.caption(f"Tarefas consultadas às {datetime.now(FUSO):%H:%M:%S} (Bahia).")
        except APIError as error:
            report_error(error)
    st.caption(
        "Para atuar em uma ordem, abra Ordens de produção no menu. Tarefas pessoais são alteradas pelo próprio responsável."
    )
