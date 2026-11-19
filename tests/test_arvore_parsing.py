import pytest
from src.search import NoParsing

@pytest.mark.parametrize(
    ("operador", "direita", "esquerda"),
    [
        ("AND", NoParsing("teste"), NoParsing("projeto")),
        ("OR", NoParsing("teste"), NoParsing("projeto")),
        ("NOT", None, NoParsing("teste")),
        ("teste", None, None)
    ],
)
def test_criacao_no_com_parametros_validos(operador, direita, esquerda):
    no = NoParsing(
        operador = operador, 
        direita = direita, 
        esquerda = esquerda
    )

    assert no.operador == operador
    assert no.direita == direita
    assert no.esquerda == esquerda


@pytest.mark.parametrize(
    ("operador", "direita", "esquerda"),
    [
        (1.0, 1.5, True),
        ("OR", NoParsing("teste"), "string"),
        ("NOT", 1, NoParsing("teste")),
    ],
)
def test_falha_criacao_no_com_parametros_tipo_incorreto(operador, direita, esquerda):
    with pytest.raises(TypeError):
        no = NoParsing(
            operador = operador, 
            direita = direita, 
            esquerda = esquerda
        )

@pytest.mark.parametrize("operador", ["¨¨", "", "TESTE", "teste\n", "teste¨"])
def test_falha_criacao_no_operador_invalido(operador):
    with pytest.raises(ValueError):
        NoParsing(operador = operador)


@pytest.mark.parametrize("operador", [1.0, None, True, ["teste"]])
def test_falha_criacao_no_operador_tipo_incorreto(operador):
    with pytest.raises(TypeError):
        NoParsing(operador = operador)


@pytest.mark.parametrize("operador", ["teste", "árvore", "abc123", "c++", "primeiro.txt"])
def test_palavra_reconhecida_no_operador(operador):
    no = NoParsing(operador = operador)

    assert no.operador == operador