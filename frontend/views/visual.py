import streamlit as st


def aplicar_estilo():
    st.html("""<style>
    [data-testid="stMainBlockContainer"] {padding-top:2rem; padding-bottom:2rem;}
    h1 {font-size:clamp(1.65rem,3vw,2.2rem) !important; line-height:1.2 !important;}
    h2 {font-size:1.5rem !important;} h3 {font-size:1.15rem !important;}
    [class*="st-key-card_urgente_"] {border-left:5px solid #B42318 !important;}
    [class*="st-key-card_normal_"] {border-left:5px solid #175CD3 !important;}
    [class*="st-key-card_"] [data-testid="stButton"] button {
        justify-content:flex-start; text-align:left; min-height:3.25rem;
        border-color:transparent; background:transparent; padding:0.5rem;
    }
    [class*="st-key-card_"] [data-testid="stButton"] button p {font-size:1.1rem; line-height:1.4; text-align:left;}
    [class*="st-key-card_"] [data-testid="stButton"] button:hover {background:#F1F5F9; border-color:#94A3B8;}
    [class*="st-key-card_"] [data-testid="stButton"] button:focus-visible {outline:3px solid #0F766E;}
    [class*="st-key-filtros_"] [data-testid="stRadio"] [role="radiogroup"] {
        flex-wrap:nowrap !important; overflow-x:auto; max-width:100%; padding-bottom:0.5rem;
    }
    [class*="st-key-filtros_"] [data-testid="stRadio"] [role="radiogroup"] label {flex-shrink:0; white-space:nowrap; border:1px solid #CBD5E1; border-radius:999px; padding:0.35rem 0.75rem; margin-right:0.25rem;}
    [class*="st-key-filtros_"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
        border-color:#0F766E; background:#E6F4EF; font-weight:600;
    }
    @media (max-width:640px) {
        [data-testid="stMainBlockContainer"] {padding:1.25rem 1rem;}
    }
    </style>""")
