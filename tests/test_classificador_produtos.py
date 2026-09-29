import pytest

from backend.services.classificador_produtos import (
    CATEGORIA_OUTROS,
    ORDEM_CATEGORIAS,
    classificar_produto,
    normalizar_texto,
    rotulo_categoria,
)


@pytest.mark.parametrize(
    ("produto", "especificacao", "observacao", "esperado"),
    [
        ("Lençol casal", "", "", "ROUPA_DE_CAMA"),
        ("lencol casal", "", "", "ROUPA_DE_CAMA"),
        ("LENÇOL CASAL", "", "", "ROUPA_DE_CAMA"),
        ("  Lençol   queen  ", "", "", "ROUPA_DE_CAMA"),
        ("Kit premium", "Toalha de banho branca", "", "BANHO"),
        ("Cortina blackout", "", "", "CORTINA"),
        ("Almofada decorativa", "", "", "ALMOFADA"),
        ("Capa de almofada", "lisa", "", "ALMOFADA"),
        ("Pano de prato", "", "", "COZINHA"),
        ("Produto especial", "sem categoria", "pedido avulso", CATEGORIA_OUTROS),
        ("", "", "", CATEGORIA_OUTROS),
    ],
)
def test_classificar_produto(produto, especificacao, observacao, esperado):
    assert classificar_produto(produto, especificacao, observacao) == esperado


def test_normalizar_remove_acentos_e_espacos():
    assert normalizar_texto("  Lençol   CASAL  ") == "lencol casal"


def test_ordem_visual_e_rotulos():
    assert ORDEM_CATEGORIAS == (
        "ROUPA_DE_CAMA",
        "BANHO",
        "COZINHA",
        "CORTINA",
        "ALMOFADA",
        "OUTROS",
    )
    assert rotulo_categoria("CORTINA") == "Cortinas"
    assert rotulo_categoria("ALMOFADA") == "Almofadas"
    assert rotulo_categoria("desconhecida") == "Outros"
