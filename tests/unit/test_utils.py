from src.utils import normaliza_query, processar_texto
import pytest

@pytest.mark.parametrize(
    ("query", "esperado"),
    [
        ("NOT TESTE", "NOT teste"),
        ("oR AND teSte", "or AND teste"),
        ("and or not", "and or not"),
        ("aNd projeto NoT trabalho", "and projeto not trabalho"),
        ("(teste OR PROJETO) AND trabaLHO", "( teste OR projeto ) AND trabalho"),
        ("       trabalho        AND       TESte  ", "trabalho AND teste"),
        ("(NOT TESTE)", "( NOT teste )"),
        ("teste(PROJETO)", "teste ( projeto )"),
        ("Árvore CIDADE123", "árvore cidade123"),
        ("", ""),
        ("        ", "")
    ],
)
def test_normaliza_query_input_validos(query, esperado):
    query_normalizada = normaliza_query(query)

    assert query_normalizada == esperado

@pytest.mark.parametrize(
    "query", [1.0, True, 10, None, [], {}]
)
def test_normaliza_query_input_tipo_invalido(query):
    with pytest.raises(TypeError):
        _ = normaliza_query(query)

class TestProcessarTexto:
    def test_extrai_palavras_e_numeros_em_minusculas_com_indices_originais(self):
        texto = "Python 312 TESTE"

        resultado = processar_texto(texto)

        assert resultado == [("python", 0), ("312", 7), ("teste", 11)]
