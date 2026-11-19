from src.classes.trie_compacta import No, prefixo_comum, TrieCompacta
import pytest


def test_inserir_filho_correto():
    no_pai = No("pai")
    no_filho = No("filho")

    no_pai.insere_filho(no_filho)

    assert len(no_pai.filhos) == 1


def test_falha_ao_inserir_filho_incorreto():
    no_pai = No("pai")
    filho_str = "oi"
    filho_int = 2
    filho_bool = True

    with pytest.raises(TypeError):
        no_pai.insere_filho(filho_str)

    with pytest.raises(TypeError):
        no_pai.insere_filho(filho_int)

    with pytest.raises(TypeError):
        no_pai.insere_filho(filho_bool)


def test_insere_documento_com_chave_e_posicao_corretas():
    no = No("base")
    chave = (1, 1)

    no.insere_documento(chave = chave, posicao_no_doc = 2)

    assert no.documentos[chave]["frequencia"] == 1
    assert no.documentos[chave]["primeira_posicao"] == 2

    no.insere_documento(chave = chave, posicao_no_doc = 3)

    assert no.documentos[chave]["frequencia"] == 2
    assert no.documentos[chave]["primeira_posicao"] == 2


def test_falha_ao_inserir_documento_chave_incorreta():
    no = No("base")
    chave_tamanho_errado = (1)
    chave_tipos_incorretos = (1.0, "teste")
    chave_valores_incorretos = (-1, -3)

    with pytest.raises(TypeError):
        no.insere_documento(chave=chave_tamanho_errado, posicao_no_doc=1)

    with pytest.raises(TypeError):
        no.insere_documento(chave=chave_tipos_incorretos, posicao_no_doc=1)

    with pytest.raises(ValueError):
        no.insere_documento(chave=chave_valores_incorretos, posicao_no_doc=1)


def test_falha_ao_inserir_documento_posicao_incorreta():
    no = No("base")
    chave_valida = (1, 2)
    posicao_tipo_incorreto = 12.5
    posicao_valor_invalido = -1

    with pytest.raises(TypeError):
        no.insere_documento(
            chave=chave_valida, 
            posicao_no_doc=posicao_tipo_incorreto
        )

    with pytest.raises(ValueError):
        no.insere_documento(
            chave=chave_valida, 
            posicao_no_doc=posicao_valor_invalido
        )


def test_no_inicializa_raiz_sem_filhos_e_documentos():
    no = No("valor")

    assert no.valor == "valor"
    assert no.filhos == []
    assert no.documentos == {}


def test_insere_filho_mantem_ordem():
    no_pai = No("pai")
    primeiro = No("primeiro")
    segundo = No("segundo")

    no_pai.insere_filho(primeiro)
    no_pai.insere_filho(segundo)

    assert no_pai.filhos == [primeiro, segundo]


def test_insere_documento_na_posicao_zero():
    no = No("base")

    no.insere_documento(chave=(0, 0), posicao_no_doc=0)

    assert no.documentos[(0, 0)] == {
        "frequencia": 1,
        "primeira_posicao": 0,
    }


def test_insere_documento_em_documentos_distintos():
    no = No("base")

    no.insere_documento(chave=(1, 1), posicao_no_doc=2)
    no.insere_documento(chave=(2, 3), posicao_no_doc=7)

    assert no.documentos[(1, 1)]["frequencia"] == 1
    assert no.documentos[(2, 3)]["frequencia"] == 1
    assert no.documentos[(1, 1)]["primeira_posicao"] == 2
    assert no.documentos[(2, 3)]["primeira_posicao"] == 7


def test_prefixo_comum_palavras_iguais():
    str_um = "teste"
    str_dois = "teste"

    prefixo = prefixo_comum(str_um, str_dois)

    assert str_um == prefixo


def test_prefixo_comum_palavras_sem_prefixo_igual():
    str_um = "teste"
    str_dois = "projeto"

    prefixo = prefixo_comum(str_um, str_dois)

    assert prefixo == ""


def test_prefixo_comum_falha_parametros_nao_sao_strings():
    str_um = 1
    str_dois = True

    with pytest.raises(TypeError):
        _ = prefixo_comum(str_um, str_dois)


@pytest.mark.parametrize(
    ("string_um", "string_dois", "esperado"),
    [
        ("abc", "abd", "ab"),
        ("ab", "abc", "ab"),
        ("abc", "ab", "ab"),
        ("x", "y", ""),
        ("", "", ""),
    ],
)
def test_prefixo_comum_diversos_tamanhos_e_prefixos(
    string_um,
    string_dois,
    esperado,
):
    assert prefixo_comum(string_um, string_dois) == esperado


@pytest.mark.parametrize(
    ("string_um", "string_dois"),
    [
        (None, "teste"),
        ("teste", None),
        (None, None),
    ],
)
def test_prefixo_comum_parametro_none_retorna_vazio(string_um, string_dois):
    assert prefixo_comum(string_um, string_dois) == ""


def test_trie_compacta_inicializa_raiz_vazia():
    trie = TrieCompacta()

    assert trie.raiz.valor == ""
    assert trie.raiz.filhos == []
    assert trie.raiz.documentos == {}


@pytest.mark.parametrize("palavra", [None, 1, True, [], {}])
def test_busca_palavra_falha_para_tipo_invalido(palavra):
    trie = TrieCompacta()

    with pytest.raises(TypeError):
        trie.busca_palavra(palavra)


@pytest.mark.parametrize(
    "palavra",
    ["", "test", "teste", "outro"],
)
def test_busca_palavra_nao_encontrada_retorna_dict_vazio(palavra):
    trie = TrieCompacta()
    trie.insere_palavra("exemplo", (1, 1), 1)

    assert trie.busca_palavra(palavra) == {}


def test_busca_palavra_respeita_maiusculas_minusculas():
    trie = TrieCompacta()
    trie.insere_palavra("Teste", (1, 1), 3)

    assert trie.busca_palavra("Teste")[(1, 1)]["primeira_posicao"] == 3
    assert trie.busca_palavra("teste") == {}


def test_insere_palavras_com_mesmo_prefixo():
    trie = TrieCompacta()
    trie.insere_palavra("teste", (1, 1), 1)
    trie.insere_palavra("testamento", (1, 2), 4)
    trie.insere_palavra("testar", (2, 1), 2)

    assert (1, 1) in trie.busca_palavra("teste")
    assert (1, 2) in trie.busca_palavra("testamento")
    assert (2, 1) in trie.busca_palavra("testar")
    assert trie.busca_palavra("test") == {}
    assert trie.busca_palavra("tester") == {}


def test_insere_palavra_que_extende_prefixo_existente():
    trie = TrieCompacta()
    trie.insere_palavra("car", (1, 1), 1)
    trie.insere_palavra("carro", (1, 2), 5)

    assert (1, 1) in trie.busca_palavra("car")
    assert (1, 2) in trie.busca_palavra("carro")
    assert trie.busca_palavra("carta") == {}


def test_insere_palavra_mais_curta_que_prefixo_existente():
    trie = TrieCompacta()
    trie.insere_palavra("testamento", (1, 1), 2)
    trie.insere_palavra("teste", (1, 2), 6)

    assert (1, 1) in trie.busca_palavra("testamento")
    assert (1, 2) in trie.busca_palavra("teste")
    assert trie.busca_palavra("testa") == {}


def test_insere_palavras_com_prefixos_independentes():
    trie = TrieCompacta()
    trie.insere_palavra("casa", (1, 1), 1)
    trie.insere_palavra("casamento", (1, 2), 3)
    trie.insere_palavra("mesa", (2, 1), 8)

    assert trie.busca_palavra("casa")[(1, 1)]["frequencia"] == 1
    assert trie.busca_palavra("casamento")[(1, 2)]["frequencia"] == 1
    assert trie.busca_palavra("mesa")[(2, 1)]["primeira_posicao"] == 8


def test_ocorrencia_mesmo_documento_atualiza_frequencia_e_posicao_inicial():
    trie = TrieCompacta()

    trie.insere_palavra("dados", (3, 4), 10)
    trie.insere_palavra("dados", (3, 4), 25)
    trie.insere_palavra("dados", (3, 4), 40)

    documentos = trie.busca_palavra("dados")

    assert documentos[(3, 4)] == {
        "frequencia": 3,
        "primeira_posicao": 10,
    }


def test_mesma_palavra_em_documentos_diferentes():
    trie = TrieCompacta()

    trie.insere_palavra("python", (1, 1), 2)
    trie.insere_palavra("python", (1, 2), 11)
    trie.insere_palavra("python", (2, 1), 0)

    documentos = trie.busca_palavra("python")

    assert set(documentos) == {(1, 1), (1, 2), (2, 1)}
    assert documentos[(1, 1)]["frequencia"] == 1
    assert documentos[(1, 2)]["primeira_posicao"] == 11
    assert documentos[(2, 1)]["primeira_posicao"] == 0