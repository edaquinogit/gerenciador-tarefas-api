"""Somente preferências e rascunhos; nunca senha, token ou permissões."""

from datetime import date, time
from uuid import UUID

from backend.services.classificador_produtos import ORDEM_CATEGORIAS

ENUMS = {
    "pagina_principal": [
        "Ordens de produção",
        "Minha conta",
        "Funcionários e setores",
        "Painel de produção",
    ],
    "ordens_etapa": ["TODAS", "PENDENTE", "CORTANDO", "COSTURANDO", "PRONTO"],
    "painel_etapa": ["TODAS", "PENDENTE", "CORTANDO", "COSTURANDO", "PRONTO"],
    "ordens_situacao": ["ativas", "coletadas", "canceladas", "todas"],
    "painel_situacao": ["ativas", "coletadas", "canceladas", "todas"],
    "ordens_categoria": ["TODAS", *ORDEM_CATEGORIAS],
    "painel_categoria": ["TODAS", *ORDEM_CATEGORIAS],
    "painel_tarefas_estado": ["Todas", "Pendentes", "Concluídas"],
    "op_unidade": ["pecas", "kits"],
    "op_prioridade": ["NORMAL", "URGENTE"],
}
PAGES = {"ordens_pagina", "painel_ordens_pagina", "painel_tarefas_pagina", "avisos_pagina"}
TEXT = {"op_produto": 150, "op_especificacao": 500, "op_observacao": 1000}
KEYS = (
    set(ENUMS)
    | PAGES
    | set(TEXT)
    | {"ordem_detalhe", "avisos_lidos", "op_quantidade", "op_dia", "op_hora", "nova_ordem_request"}
)


def validar_estado(values):
    if isinstance(values, dict):
        values = dict(values)
        if values.get("pagina_principal") == "Minhas tarefas":
            values["pagina_principal"] = "Ordens de produção"
        elif values.get("pagina_principal") == "Todas as tarefas":
            values["pagina_principal"] = "Painel de produção"
    if not isinstance(values, dict) or set(values) - KEYS:
        raise ValueError("Estado de navegação inválido")
    result = {}
    for key, value in values.items():
        valid = False
        if key in ENUMS:
            valid = value in ENUMS[key]
        elif key == "ordem_detalhe":
            valid = type(value) is int and 0 <= value <= 2147483647
        elif key in PAGES or key == "op_quantidade":
            valid = type(value) is int and 1 <= value <= 1000000
        elif key in TEXT:
            valid = isinstance(value, str) and len(value) <= TEXT[key]
        elif key == "avisos_lidos":
            valid = type(value) is bool
        elif key == "op_dia":
            date.fromisoformat(value)
            valid = True
        elif key == "op_hora":
            time.fromisoformat(value)
            valid = True
        elif key == "nova_ordem_request":
            UUID(value)
            valid = True
        if not valid:
            raise ValueError("Preferência inválida")
        result[key] = value
    return result
