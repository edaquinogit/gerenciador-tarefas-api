import streamlit as st

from frontend.services.task_service import APIError
from frontend.session import persist_state
from frontend.views.ordens import horario, selecionar_ordem
from frontend.views.paginacao import carregar_pagina, render_paginacao, reset_page


@st.fragment(run_every="10s")
def render_avisos(service, token, report_error):
    try:
        resumo = service.notificacoes(token, limit=1)
    except APIError as error:
        report_error(error)
        st.caption(
            "Avisos temporariamente indisponíveis. A consulta será repetida automaticamente."
        )
        return
    st.caption(f"Avisos não lidos: {resumo['nao_lidas']}")
    destaque = st.empty()
    if resumo["nao_lidas"]:
        destaque.info(
            f"Você tem {resumo['nao_lidas']} aviso(s) de produtos prontos. Confira a situação de coleta abaixo."
        )
    with st.expander("Avisos de produtos prontos", expanded=bool(resumo["nao_lidas"])):
        st.caption(
            "Atualização automática a cada 10 segundos com a sessão ativa. Ler não confirma coleta."
        )
        mostrar_lidos = st.checkbox(
            "Incluir avisos lidos",
            key="avisos_lidos",
            on_change=reset_page,
            args=("avisos_pagina",),
        )
        try:
            caixa, pagina, paginas = carregar_pagina(
                lambda **kwargs: service.notificacoes(token, **kwargs),
                "avisos_pagina",
                tamanho=10,
                somente_nao_lidas=not mostrar_lidos,
            )
            render_paginacao("avisos_pagina", pagina, paginas, caixa["total"], tamanho=10)
        except APIError as error:
            report_error(error)
            return
        if not caixa["itens"]:
            st.info("Nenhum aviso nesta página.")
        for aviso in caixa["itens"]:
            st.text(aviso["mensagem"])
            if st.button(
                "Abrir ordem",
                key=f"aviso_ordem_{aviso['id']}",
                on_click=selecionar_ordem,
                args=(aviso["ordem_id"],),
            ):
                st.rerun()
            st.caption(horario(aviso["criado_em"]))
            if aviso["situacao"] == "AGUARDANDO_COLETA":
                st.success("Disponível para coleta e embalagem.")
            elif aviso["situacao"] == "COLETADA":
                st.caption("Lote já coletado. Este aviso permanece no histórico.")
            elif aviso["situacao"] == "CANCELADA":
                st.warning("Ordem cancelada. Não coletar este lote com base neste aviso.")
            else:
                st.caption("Ordem em produção. Confira a situação atual na fila.")
            if aviso["lida_em"] is None:
                if st.button("Marcar como lido", key=f"aviso_lido_{aviso['id']}"):
                    try:
                        service.ler_notificacao(aviso["id"], token)
                        st.rerun()
                    except APIError as error:
                        report_error(error)
            else:
                st.caption(f"Lido em {horario(aviso['lida_em'])}")

    persist_state(service)
