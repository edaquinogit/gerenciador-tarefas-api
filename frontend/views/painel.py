from datetime import datetime

import streamlit as st

from frontend.services.task_service import APIError
from frontend.session import persist_state
from frontend.views.filtros import render_filtros
from frontend.views.ordens import FUSO, render_cards
from frontend.views.paginacao import carregar_pagina, render_paginacao


@st.fragment(run_every="10s")
def render_painel(service, token, user, report_error):
    token = st.session_state.get("access_token", token)
    st.title("Painel de produção")
    st.caption("Todas as ordens entre setores · atualização automática a cada 10 segundos.")
    st.button("Atualizar agora", key="painel_atualizar")
    etapa, situacao, categoria = render_filtros(
        "painel", "painel_ordens_pagina", situacao_inicial="todas"
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
        render_paginacao("painel_ordens_pagina", page, pages, result["total"])
        render_cards(service, token, user, report_error, result["itens"])
        if not result["itens"]:
            st.info("Nenhuma ordem encontrada para os filtros selecionados.")
        st.caption(
            f"Ordens consultadas às {datetime.now(FUSO):%H:%M:%S} (Bahia). Urgentes primeiro, depois prazo."
        )
    except APIError as error:
        report_error(error)
    persist_state(service)
