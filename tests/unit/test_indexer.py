from src.classes.indexer import ler_documentos
import pytest

class TestLerDocumentos:
    def test_carrega_arquivos_txt_em_multiplas_categorias_com_latin1(self, tmp_path):
        cat_business = tmp_path / "business"
        cat_sport = tmp_path / "sport"
        cat_business.mkdir()
        cat_sport.mkdir()

        (cat_business / "001.txt").write_bytes("Ação e mercado".encode("latin-1"))
        (cat_sport / "002.txt").write_bytes("Campeão nacional".encode("latin-1"))
        
        documentos = ler_documentos(str(tmp_path))

        resultado = {(d.categoria, d.doc_id, d.conteudo) for d in documentos}
        assert resultado == {("business", "001", "Ação e mercado"), ("sport", "002", "Campeão nacional")}

    def test_retorna_lista_vazia_quando_corpus_esta_vazio(self, tmp_path):
        documentos = ler_documentos(str(tmp_path))

        assert documentos == []

    def test_ignora_arquivos_soltos_na_raiz_do_corpus(self, tmp_path):
        (tmp_path / "001.txt").write_text("ignorado", encoding="latin-1")

        documentos = ler_documentos(str(tmp_path))
        assert documentos == []

    def test_ignora_arquivos_que_nao_terminam_com_txt_minusculo(self, tmp_path):
        cat = tmp_path / "tech"
        cat.mkdir()
        (cat / "001.txt").write_text("valido", encoding="latin-1")
        (cat / "002.csv").write_text("ignorado", encoding="latin-1")
        (cat / "003.TXT").write_text("ignorado", encoding="latin-1")

        documentos = ler_documentos(str(tmp_path))

        assert len(documentos) == 1
        assert documentos[0].doc_id == "001"

    def test_continua_leitura_quando_um_item_falha_ao_abrir(self, tmp_path):
        cat = tmp_path / "politics"
        cat.mkdir()
        (cat / "001.txt").mkdir() # Força IsADirectoryError no open()
        (cat / "002.txt").write_text("texto valido", encoding="latin-1")

        documentos = ler_documentos(str(tmp_path))

        assert len(documentos) == 1
        assert documentos[0].doc_id == "002"

    def test_lanca_erro_quando_diretorio_corpus_nao_existe(self, tmp_path):
        caminho_inexistente = tmp_path / "inexistente"

        with pytest.raises(FileNotFoundError):
            ler_documentos(str(caminho_inexistente))

class TestConstruirIndice:
    def test_indexa_documentos_na_trie_e_calcula_estatisticas_para_multiplos_docs(self, tmp_path):
        (tmp_path / "business").mkdir()
        (tmp_path / "sport").mkdir()
        (tmp_path / "business" / "001.txt").write_text("trade trade market", encoding="latin-1")
        (tmp_path / "sport" / "002.txt").write_text("market", encoding="latin-1")
        corpus = Corpus()

        corpus.construir_indice(str(tmp_path))

        doc1 = (Categoria.business.value, 1)
        doc2 = (Categoria.sport.value, 2)
        assert corpus.todos_documentos == {doc1, doc2}
        assert corpus.trie.busca_palavra("trade") == {doc1: {"frequencia": 2, "primeira_posicao": 0}}
        assert corpus.estatisticas_corpus["trade"]["media"] == pytest.approx(1.0)
        assert corpus.estatisticas_corpus["trade"]["desvio_padrao"] == pytest.approx(math.sqrt(2))
        assert corpus.estatisticas_corpus["market"]["media"] == pytest.approx(1.0)
        assert corpus.estatisticas_corpus["market"]["desvio_padrao"] == pytest.approx(0.0)

    def test_define_desvio_padrao_zero_quando_ha_apenas_um_documento(self, tmp_path):
        (tmp_path / "tech").mkdir()
        (tmp_path / "tech" / "010.txt").write_text("python python", encoding="latin-1")
        corpus = Corpus()

        corpus.construir_indice(str(tmp_path))

        assert corpus.estatisticas_corpus["python"] == {"media": 2.0, "desvio_padrao": 0}
