from src.snippet import gerar_snippet_formatado, destacar_termos_no_snippet
import pytest

MAPA_CATEGORIAS = {1: "business"}


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
