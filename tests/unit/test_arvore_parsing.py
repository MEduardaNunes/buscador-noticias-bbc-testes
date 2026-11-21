import pytest
from src.busca import ArvoreParsing, NoParsing

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



def test_token_atual_retorna_none_apos_fim():
    arvore = ArvoreParsing("teste")

    arvore.consome_token()

    assert arvore.token_atual() is None


def test_consume_token_rejeita_fim_inesperado():
    arvore = ArvoreParsing("NOT")
    arvore.consome_token("NOT")

    with pytest.raises(ValueError, match="Fim inesperado de tokens"):
        arvore.consome_token("teste")


def test_consume_token_rejeita_token_diferente():
    arvore = ArvoreParsing("teste")

    with pytest.raises(ValueError, match="Token esperado"):
        arvore.consome_token("AND")


def test_parse_or_retorna_none_sem_primeira_expressao(monkeypatch):
    arvore = ArvoreParsing("a")
    monkeypatch.setattr(arvore, "parse_and", lambda: None)

    assert arvore.parse_or() is None


def test_parse_or_rejeita_expressao_ausente_apos_or(monkeypatch):
    arvore = ArvoreParsing("a OR")
    arvore.pos = 1
    resultados = iter([NoParsing("a"), None])
    monkeypatch.setattr(arvore, "parse_and", lambda: next(resultados))

    with pytest.raises(ValueError, match="após OR"):
        arvore.parse_or()


def test_parse_and_retorna_none_sem_primeira_expressao(monkeypatch):
    arvore = ArvoreParsing("a")
    monkeypatch.setattr(arvore, "parse_not", lambda: None)

    assert arvore.parse_and() is None


def test_parse_and_rejeita_expressao_ausente_apos_and(monkeypatch):
    arvore = ArvoreParsing("a AND")
    arvore.pos = 1
    resultados = iter([NoParsing("a"), None])
    monkeypatch.setattr(arvore, "parse_not", lambda: next(resultados))

    with pytest.raises(ValueError, match="após AND"):
        arvore.parse_and()


def test_parse_not_rejeita_not_sem_expressao():
    arvore = ArvoreParsing("NOT")

    with pytest.raises(ValueError, match="após NOT"):
        arvore.gera_parsing_tokens()


def test_parse_not_rejeita_expressao_nula(monkeypatch):
    arvore = ArvoreParsing("NOT a")
    arvore.pos = 0
    monkeypatch.setattr(arvore, "parse_not", lambda: None)

    with pytest.raises(ValueError, match="após NOT"):
        ArvoreParsing.parse_not(arvore)


def test_parenteses_rejeitam_expressao_nula(monkeypatch):
    arvore = ArvoreParsing("(a)")
    arvore.pos = 0
    monkeypatch.setattr(arvore, "parse_exp", lambda: None)

    with pytest.raises(ValueError, match="Expressão do parênteses não existe"):
        arvore.parse_subexp()


def test_gera_parsing_rejeita_expressao_nula(monkeypatch):
    arvore = ArvoreParsing("a")
    monkeypatch.setattr(arvore, "parse_exp", lambda: None)

    with pytest.raises(ValueError, match="parsing falhou"):
        arvore.gera_parsing_tokens()


@pytest.mark.parametrize("query", ["a OR", "a AND", "NOT"])
def test_operadores_sem_expressao_rejeitam_consulta(query):
    arvore = ArvoreParsing(query)

    with pytest.raises(ValueError):
        arvore.gera_parsing_tokens()
