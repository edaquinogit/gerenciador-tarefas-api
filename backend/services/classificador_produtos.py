"""Classificação determinística de produtos por palavras-chave."""

from __future__ import annotations

import re
import unicodedata

CATEGORIA_OUTROS = "OUTROS"

ORDEM_CATEGORIAS: tuple[str, ...] = (
    "ROUPA_DE_CAMA",
    "BANHO",
    "COZINHA",
    "CORTINA",
    "ALMOFADA",
    CATEGORIA_OUTROS,
)

ROTULOS_CATEGORIA: dict[str, str] = {
    "ROUPA_DE_CAMA": "Roupa de cama",
    "BANHO": "Banho",
    "COZINHA": "Cozinha",
    "CORTINA": "Cortinas",
    "ALMOFADA": "Almofadas",
    CATEGORIA_OUTROS: "Outros",
}

# Palavras-chave por categoria (já sem acento, lowercase). Ordem: mais específicas primeiro.
_PALAVRAS_CHAVE: dict[str, tuple[str, ...]] = {
    "ROUPA_DE_CAMA": (
        "cobre leito",
        "cobre leitos",
        "cobreleito",
        "cobreleitos",
        "lencol",
        "lencois",
        "fronha",
        "fronhas",
        "colcha",
        "colchas",
        "edredom",
        "edredons",
    ),
    "BANHO": (
        "toalha",
        "toalhas",
        "banho",
        "rosto",
        "piso",
    ),
    "COZINHA": (
        "pano de prato",
        "guardanapo",
        "guardanapos",
        "cozinha",
        "avental",
        "aventais",
    ),
    "CORTINA": (
        "blackout",
        "cortina",
        "cortinas",
        "voil",
    ),
    "ALMOFADA": (
        "capa de almofada",
        "almofada",
        "almofadas",
    ),
}


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def rotulo_categoria(codigo: str) -> str:
    return ROTULOS_CATEGORIA.get(codigo, ROTULOS_CATEGORIA[CATEGORIA_OUTROS])


def classificar_produto(
    produto: str,
    especificacao: str = "",
    observacao: str = "",
) -> str:
    # O nome do produto tem prioridade sobre detalhes e observações.
    for campo in (produto, especificacao, observacao):
        texto = normalizar_texto(campo)
        if not texto:
            continue
        # A expressão específica evita confundir mesa com toalhas de banho.
        if re.search(r"\btoalhas? de mesa\b", texto):
            return "COZINHA"
        for categoria in ORDEM_CATEGORIAS:
            if categoria == CATEGORIA_OUTROS:
                continue
            for palavra in _PALAVRAS_CHAVE[categoria]:
                if re.search(r"\b" + re.escape(palavra) + r"\b", texto):
                    return categoria
    return CATEGORIA_OUTROS
