"""Navegação compartilhada; estado independente dos widgets e limitado pelos dados."""

import streamlit as st

from frontend.services.task_service import APIError


def reset_page(key):
    st.session_state[key] = 1


def carregar_pagina(consultar, key, tamanho=20, **filtros):
    pagina = max(1, int(st.session_state.get(key, 1)))
    # Consulta novamente ao encolher a lista; limite evita loop sob alterações contínuas.
    for _ in range(3):
        resultado = consultar(offset=(pagina - 1) * tamanho, limit=tamanho, **filtros)
        paginas = max(1, (resultado["total"] + tamanho - 1) // tamanho)
        if pagina <= paginas:
            st.session_state[key] = pagina
            return resultado, pagina, paginas
        pagina = paginas
        st.session_state[key] = pagina
    raise APIError("A lista mudou durante a consulta. Atualize para carregar a página atual.")


def mudar_pagina(key, destino):
    st.session_state[key] = destino


def render_paginacao(key, pagina, paginas, total, tamanho=20):
    anterior, resumo, proxima = st.columns([1, 3, 1])
    anterior.button(
        "Anterior",
        key=f"{key}_anterior",
        disabled=pagina <= 1,
        on_click=mudar_pagina,
        args=(key, pagina - 1),
        width="stretch",
    )
    inicio = (pagina - 1) * tamanho + 1 if total else 0
    fim = min(pagina * tamanho, total)
    rotulo = "registro" if total == 1 else "registros"
    resumo.caption(f"Página {pagina} de {paginas} • {total} {rotulo} • exibindo {inicio}–{fim}")
    proxima.button(
        "Próxima",
        key=f"{key}_proxima",
        disabled=pagina >= paginas,
        on_click=mudar_pagina,
        args=(key, pagina + 1),
        width="stretch",
    )
