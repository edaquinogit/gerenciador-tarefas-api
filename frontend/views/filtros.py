import streamlit as st

from backend.services.classificador_produtos import ORDEM_CATEGORIAS, rotulo_categoria

ETAPAS = {
    "TODAS": "Todas",
    "PENDENTE": "Pendente",
    "CORTANDO": "Cortando",
    "COSTURANDO": "Costurando",
    "PRONTO": "Pronto",
}


def mudar_filtro(prefix, page):
    if st.session_state.get(f"{prefix}_etapa") is None:
        st.session_state[f"{prefix}_etapa"] = "TODAS"
    st.session_state[page] = 1


def limpar_filtros(prefix, page, etapa, situacao):
    st.session_state.update(
        {
            f"{prefix}_etapa": etapa,
            f"{prefix}_situacao": situacao,
            f"{prefix}_categoria": "TODAS",
            page: 1,
        }
    )


def render_filtros(prefix, page, etapa_inicial="TODAS", situacao_inicial="ativas"):
    with st.container(key=f"filtros_{prefix}"):
        etapa = st.radio(
            "Etapa",
            list(ETAPAS),
            index=list(ETAPAS).index(etapa_inicial),
            horizontal=True,
            format_func=ETAPAS.get,
            key=f"{prefix}_etapa",
            width="stretch",
            on_change=mudar_filtro,
            args=(prefix, page),
        )
        with st.expander("Mais filtros"):
            cols = st.columns(2)
            situacao = cols[0].selectbox(
                "Situação",
                ["ativas", "coletadas", "canceladas", "todas"],
                index=["ativas", "coletadas", "canceladas", "todas"].index(situacao_inicial),
                format_func=str.title,
                key=f"{prefix}_situacao",
                on_change=mudar_filtro,
                args=(prefix, page),
            )
            categoria = cols[1].selectbox(
                "Categoria",
                ["TODAS", *ORDEM_CATEGORIAS],
                format_func=lambda v: "Todas" if v == "TODAS" else rotulo_categoria(v),
                key=f"{prefix}_categoria",
                on_change=mudar_filtro,
                args=(prefix, page),
            )
        st.caption(
            f"{situacao.title()} · {rotulo_categoria(categoria) if categoria != 'TODAS' else 'Todas as categorias'}"
        )
        st.button(
            "Limpar filtros",
            key=f"{prefix}_limpar",
            on_click=limpar_filtros,
            args=(prefix, page, etapa_inicial, situacao_inicial),
        )
    return etapa or "TODAS", situacao, categoria
