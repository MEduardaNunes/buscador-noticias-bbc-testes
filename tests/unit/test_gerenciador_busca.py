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

    def test_or_retorna_documentos_com_qualquer_um_dos_termos(self, gerenciador):
        resultados = gerenciador.executar_busca("gas OR phone")

        assert ids_retornados(resultados) == {"business/003", "tech/004"}

    def test_not_exclui_documentos_que_contem_o_termo(self, gerenciador):
        resultados = gerenciador.executar_busca("prices AND NOT oil")

        assert ids_retornados(resultados) == {"business/003"}

    def test_ignora_maiusculas_nos_termos_da_consulta(self, gerenciador):
        resultados = gerenciador.executar_busca("GAS")

        assert ids_retornados(resultados) == {"business/003"}

    @pytest.mark.parametrize("consulta", ["oil AND", "(oil OR gas", "AND prices", ""])
    def test_consulta_com_sintaxe_invalida_retorna_lista_vazia(self, gerenciador, consulta):
        resultados = gerenciador.executar_busca(consulta)

        assert resultados == []

    def test_termo_inexistente_no_corpus_retorna_lista_vazia(self, gerenciador):
        resultados = gerenciador.executar_busca("football")

        assert resultados == []

    def test_ordena_resultados_por_relevancia_decrescente(self, gerenciador):
        resultados = gerenciador.executar_busca("oil")

        ids_em_ordem = [resultado["id_completo"] for resultado in resultados]
        assert ids_em_ordem == ["business/001", "business/002"]
        assert float(resultados[0]["score"]) > float(resultados[1]["score"])

    def test_pagina_resultados_pelo_tamanho_informado(self, gerenciador):
        primeira_pagina = gerenciador.executar_busca("prices OR oil OR grow", num_pagina=1, tamanho_pagina=2)
        segunda_pagina = gerenciador.executar_busca("prices OR oil OR grow", num_pagina=2, tamanho_pagina=2)

        assert len(primeira_pagina) == 2
        assert len(segunda_pagina) == 2
        assert ids_retornados(primeira_pagina).isdisjoint(ids_retornados(segunda_pagina))

    def test_formata_resultado_com_identificadores_e_snippet_destacado(self, gerenciador):
        resultado = gerenciador.executar_busca("gas")[0]

        assert resultado["id_completo"] == "business/003"
        assert resultado["categoria"] == "business"
        assert resultado["id_num"] == "003"
        assert resultado["snippet"] == "<b>Gas</b> prices fall"
