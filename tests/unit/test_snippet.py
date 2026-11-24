from src.snippet import (
    destacar_termos_no_snippet,
    gerar_snippet_formatado,
    gerar_snippet_primeiras_frases,
)
import pytest

MAPA_CATEGORIAS = {1: "business"}


def test_gerar_snippet_primeiras_frases_ignora_titulo_e_limita_duas_frases():
    conteudo = "Título do artigo\n\nPrimeira frase. Segunda frase! Terceira frase."

    snippet = gerar_snippet_primeiras_frases(conteudo)

    assert snippet == "Primeira frase. Segunda frase!"


@pytest.fixture
def caminho_corpus(tmp_path):
    (tmp_path / "business").mkdir()
    return tmp_path


def criar_documento(caminho_corpus, numero, conteudo):
    """Cria o arquivo business/<numero>.txt e devolve o doc_id correspondente."""
    (caminho_corpus / "business" / f"{numero:03d}.txt").write_text(conteudo, encoding="latin-1")
    return (1, numero)


class TestGerarSnippetFormatado:
    def test_recorta_80_caracteres_ao_redor_do_termo_com_reticencias(self, caminho_corpus):
        antes, depois = "a" * 100, "b" * 100
        doc_id = criar_documento(caminho_corpus, 1, f"{antes} economy {depois}")

        snippet = gerar_snippet_formatado(doc_id, "economy", 101, str(caminho_corpus), MAPA_CATEGORIAS, ["economy"])

        assert snippet == "... " + "a" * 79 + " <b>economy</b> " + "b" * 79 + " ..."

    def test_omite_reticencias_quando_documento_cabe_inteiro_no_snippet(self, caminho_corpus):
        doc_id = criar_documento(caminho_corpus, 1, "Economy grows.")

        snippet = gerar_snippet_formatado(doc_id, "economy", 0, str(caminho_corpus), MAPA_CATEGORIAS, ["economy"])

        assert snippet == "<b>Economy</b> grows."

    @pytest.mark.parametrize("indice_incorreto", [0, 999])
    def test_localiza_termo_pelo_texto_quando_indice_nao_corresponde(self, caminho_corpus, indice_incorreto):
        doc_id = criar_documento(caminho_corpus, 1, "The economy is growing")

        snippet = gerar_snippet_formatado(doc_id, "economy", indice_incorreto, str(caminho_corpus), MAPA_CATEGORIAS, ["economy"])

        assert snippet == "The <b>economy</b> is growing"

    def test_informa_quando_termo_nao_esta_no_documento(self, caminho_corpus):
        doc_id = criar_documento(caminho_corpus, 1, "The economy is growing")

        snippet = gerar_snippet_formatado(doc_id, "football", 0, str(caminho_corpus), MAPA_CATEGORIAS, ["football"])

        assert snippet == "[Termo de foco não encontrado no documento]"

    def test_informa_quando_documento_nao_existe(self, caminho_corpus):
        doc_inexistente = (1, 999)

        snippet = gerar_snippet_formatado(doc_inexistente, "economy", 0, str(caminho_corpus), MAPA_CATEGORIAS, ["economy"])

        assert snippet == "[Documento não encontrado]"


class TestDestacarTermosNoSnippet:
    def test_destaca_todas_as_ocorrencias_ignorando_maiusculas(self):
        destacado = destacar_termos_no_snippet("Oil prices and OIL demand", ["oil", "demand"])

        assert destacado == "<b>Oil</b> prices and <b>OIL</b> <b>demand</b>"

    def test_nao_aninha_destaque_quando_um_termo_contem_outro(self):
        destacado = destacar_termos_no_snippet("growth of 40% and 5%", ["%", "40%"])

        assert destacado == "growth of <b>40%</b> and 5<b>%</b>"

    def test_nao_destaca_termo_dentro_de_outra_palavra(self):
        destacado = destacar_termos_no_snippet("corporate rate", ["rate"])

        assert destacado == "corporate <b>rate</b>"
