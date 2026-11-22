from src.busca import GerenciadorDeBusca
from src.classes.indexer import Corpus
import pytest

DOCUMENTOS = {
    ("business", "001"): "Oil prices rise as oil demand grows",
    ("business", "002"): "Oil companies report profits",
    ("business", "003"): "Gas prices fall",
    ("tech", "004"): "New phone sales grow",
}


@pytest.fixture
def gerenciador(tmp_path):
    """Indexa um corpus pequeno em disco e devolve um GerenciadorDeBusca sobre ele."""
    for (categoria, numero), conteudo in DOCUMENTOS.items():
        (tmp_path / categoria).mkdir(exist_ok=True)
        (tmp_path / categoria / f"{numero}.txt").write_text(conteudo, encoding="latin-1")

    corpus = Corpus()
    corpus.construir_indice(str(tmp_path))

    return GerenciadorDeBusca(corpus.trie, corpus.todos_documentos, str(tmp_path), corpus.estatisticas_corpus)


def ids_retornados(resultados):
    return {resultado["id_completo"] for resultado in resultados}


class TestExecutarBusca:
    def test_and_retorna_apenas_documentos_com_todos_os_termos(self, gerenciador):
        resultados = gerenciador.executar_busca("oil AND prices")

        assert ids_retornados(resultados) == {"business/001"}
