from src.classes.trie_compacta import No
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