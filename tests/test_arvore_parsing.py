import pytest
from src.search import ArvoreParsing, NoParsing

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


def test_arvore_mantem_ordem_esquerda_direita_em_and():
    arvore = ArvoreParsing("a AND b")

    raiz = arvore.gera_parsing_tokens()

    assert raiz.operador == "AND"
    assert raiz.esquerda.operador == "a"
    assert raiz.direita.operador == "b"


def test_arvore_mantem_ordem_esquerda_direita_em_or():
    arvore = ArvoreParsing("a OR b")

    raiz = arvore.gera_parsing_tokens()

    assert raiz.operador == "OR"
    assert raiz.esquerda.operador == "a"
    assert raiz.direita.operador == "b"


def test_arvore_respeita_precedencia_not_and_or():
    arvore = ArvoreParsing("NOT a AND b OR c")

    raiz = arvore.gera_parsing_tokens()

    assert raiz.operador == "OR"
    assert raiz.esquerda.operador == "AND"
    assert raiz.esquerda.esquerda.operador == "NOT"
    assert raiz.esquerda.direita.operador == "b"
    assert raiz.direita.operador == "c"


def test_arvore_respeita_parenteses():
    arvore = ArvoreParsing("(a OR b) AND c")

    raiz = arvore.gera_parsing_tokens()

    assert raiz.operador == "AND"
    assert raiz.esquerda.operador == "OR"
    assert raiz.esquerda.esquerda.operador == "a"
    assert raiz.esquerda.direita.operador == "b"
    assert raiz.direita.operador == "c"


def test_gera_parsing_tokens_pode_ser_chamada_novamente():
    arvore = ArvoreParsing("a AND b")

    primeira_raiz = arvore.gera_parsing_tokens()
    segunda_raiz = arvore.gera_parsing_tokens()

    assert segunda_raiz is not primeira_raiz
    assert repr(segunda_raiz) == "(a AND b)"


@pytest.mark.parametrize(
    "query",
    ["", "a b", "a AND", "AND a", "()", "(a", "a)", "a OR OR b"],
)
def test_arvore_rejeita_consulta_invalida(query):
    arvore = ArvoreParsing(query)

    with pytest.raises(ValueError):
        arvore.gera_parsing_tokens()


@pytest.mark.parametrize("query", [1.0, None, True, ["a"]])
def test_arvore_rejeita_query_tipo_incorreto(query):
    with pytest.raises(TypeError):
        ArvoreParsing(query)
