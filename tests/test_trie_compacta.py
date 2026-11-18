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