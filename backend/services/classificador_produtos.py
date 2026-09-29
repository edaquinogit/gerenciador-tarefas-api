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
        "lencol",
        "fronha",
        "colcha",
        "edredom",
    ),
    "BANHO": (
        "toalha",
        "banho",
        "rosto",
        "piso",
    ),
    "COZINHA": (
        "pano de prato",
        "guardanapo",
        "cozinha",
        "avental",
    ),
    "CORTINA": (
        "blackout",
        "cortina",
        "voil",
    ),
    "ALMOFADA": (
        "capa de almofada",
        "almofada",
    ),
}


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def rotulo_categoria(codigo: str) -> str:
    return ROTULOS_CATEGORIA.get(codigo, ROTULOS_CATEGORIA[CATEGORIA_OUTROS])


def classificar_produto(
    produto: str,
    especificacao: str = "",
    observacao: str = "",
) -> str:
    texto = normalizar_texto(f"{produto} {especificacao} {observacao}")
    if not texto:
        return CATEGORIA_OUTROS
    for categoria in ORDEM_CATEGORIAS:
        if categoria == CATEGORIA_OUTROS:
            continue
        for palavra in _PALAVRAS_CHAVE[categoria]:
            if palavra in texto:
                return categoria
    return CATEGORIA_OUTROS
