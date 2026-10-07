import os
from datetime import date, datetime, time
from pathlib import Path
from uuid import uuid4

import streamlit as st
from streamlit.components.v1 import declare_component

from frontend.services.task_service import APIError
from shared.ui_state import KEYS, validar_estado

_bridge = declare_component(
    "sessao_browser", path=str(Path(__file__).parent / "components/session")
)


def browser_session(**kwargs):
    return _bridge(
        api_url=os.getenv("PUBLIC_API_URL", ""),
        api_port=int(os.getenv("PUBLIC_API_PORT", "8000")),
        key="sessao_browser",
        default=None,
        **kwargs,
    )


def restore_state(values, only_missing=False):
    try:
        values = validar_estado(values)
    except (ValueError, TypeError):
        values = {}
    st.session_state["saved_ui"] = dict(values)
    for key, value in values.items():
        if only_missing and key in st.session_state:
            continue
        if key == "op_dia":
            value = date.fromisoformat(value)
        elif key == "op_hora":
            value = time.fromisoformat(value)
        st.session_state[key] = value


def persist_state(service, *, required=False):
    token = st.session_state.get("access_token")
    if not token or not st.session_state.get("ui_loaded"):
        return
    previous = st.session_state.get("saved_ui", {})
    values = dict(previous)
    for key in KEYS:
        if key in st.session_state:
            value = st.session_state[key]
            value = value.isoformat() if isinstance(value, (date, time)) else value
            try:
                validar_estado({key: value})
            except (ValueError, TypeError):
                # Campos de data podem ficar vazios durante a edição.
                values.pop(key, None)
                continue
            values[key] = value
    if values == previous:
        return
    try:
        service.salvar_estado(token, validar_estado(values))
        st.session_state["saved_ui"] = values
    except APIError:
        if required:
            raise
        st.warning(
            "Não foi possível salvar a navegação e o rascunho. Mantenha esta aba aberta e tente novamente."
        )


def reset_local(message):
    st.session_state.clear()
    st.session_state["clear_cookie"] = str(uuid4())
    st.session_state["flash"] = message


def logout(service):
    try:
        service.sair(st.session_state.access_token)
    except APIError as error:
        if error.status_code != 401:
            st.session_state["logout_error"] = (
                "Não foi possível encerrar a sessão. Tente Sair novamente."
            )
            return
    reset_local("Você saiu do sistema.")


def recover_session():
    """Um JWT vencido não encerra prematuramente uma sessão de navegador válida."""
    if st.session_state.get("session_expires") and not st.session_state.get("awaiting_restore"):
        st.session_state.pop("access_token", None)
        st.session_state["restore_request"] = str(uuid4())
        st.session_state["awaiting_restore"] = True
        st.rerun()
    reset_local("Sua sessão foi encerrada ou expirou. Entre novamente.")
    st.rerun()


@st.fragment
def sync_session(service):
    # Renovar o JWT não deve reconstruir campos ainda em edição no navegador.
    def navigation_state():
        return tuple(
            bool(st.session_state.get(key))
            for key in (
                "access_token",
                "bridge_event",
                "ui_loaded",
                "browser_code",
                "clear_cookie",
                "awaiting_restore",
            )
        ) + (st.session_state.get("session_user"),)

    before = navigation_state()
    try:
        _sync_session(service)
    except APIError as error:
        if error.status_code == 401 and st.session_state.get("access_token"):
            recover_session()
        st.error(str(error))
        st.stop()
    if before != navigation_state():
        st.rerun()


def _sync_session(service):
    result = browser_session(
        code=st.session_state.get("browser_code"),
        clear=st.session_state.get("clear_cookie"),
        force=st.session_state.get("restore_request"),
        session_id=st.session_state.get("browser_session_id"),
    )
    if result and result.get("event") != st.session_state.get("bridge_event"):
        st.session_state["bridge_event"] = result.get("event")
        status = result.get("status")
        if status == "authenticated" and not st.session_state.get("clear_cookie"):
            # Valida identidade e acesso no servidor antes de restaurar a interface.
            user = service.me(result["access_token"])
            fresh = not st.session_state.get("access_token")
            recovering = st.session_state.pop("awaiting_restore", False)
            changed_user = st.session_state.get("session_user") not in (None, user["id"])
            if changed_user:
                st.session_state.clear()
                st.session_state["bridge_event"] = result.get("event")
            st.session_state["session_user"] = user["id"]
            st.session_state.access_token = result["access_token"]
            st.session_state["session_expires"] = result["expires_at"]
            st.session_state.pop("browser_code", None)
            st.session_state.pop("session_error", None)
            if (fresh and not recovering) or changed_user:
                restore_state(result.get("state", {}))
                st.session_state["ui_loaded"] = True
        elif status == "guest":
            st.session_state.pop("session_error", None)
            if result.get("claim_failed"):
                st.session_state["session_error"] = (
                    "Não foi possível manter este login após atualizar a página. Saia e entre novamente para recuperar a sessão persistente."
                )
                st.session_state.pop("browser_code", None)
            if st.session_state.get("awaiting_restore") or (
                st.session_state.get("access_token") and st.session_state.get("session_expires")
            ):
                reset_local("Sua sessão foi encerrada ou expirou. Entre novamente.")
                st.rerun()
            st.session_state.pop("clear_cookie", None)
        elif status == "error":
            st.session_state["session_error"] = (
                "Não foi possível recuperar a sessão no navegador. Verifique a conexão e a configuração de acesso."
            )
    if st.session_state.get("session_error"):
        st.warning(st.session_state.session_error)
    if st.session_state.get("awaiting_restore"):
        st.info("Reconectando sua sessão…")
        st.stop()
    if not result and not st.session_state.get("access_token"):
        st.info("Verificando sua sessão…")
        st.stop()
    if st.session_state.get("access_token") and not st.session_state.get("ui_loaded"):
        service.me(st.session_state.access_token)
        restore_state(service.estado(st.session_state.access_token)["state"])
        st.session_state["ui_loaded"] = True
    elif st.session_state.get("ui_loaded"):
        restore_state(st.session_state.get("saved_ui", {}), only_missing=True)
    if expiry := st.session_state.get("session_expires"):
        remaining = datetime.fromisoformat(expiry).timestamp() - datetime.now().timestamp()
        if 0 < remaining < 900:
            st.warning(
                "Sua sessão termina em menos de 15 minutos. Salve seu trabalho e entre novamente ao encerrar."
            )
