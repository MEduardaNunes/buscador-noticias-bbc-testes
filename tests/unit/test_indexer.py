from src.classes.indexer import ler_documentos, Corpus, Categoria
import pytest
import math

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
    def test_indexa_documentos_e_ocorrencias_na_trie(self, tmp_path):
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
        assert corpus.trie.busca_palavra("market") == {doc1: {"frequencia": 1, "primeira_posicao": 12}, doc2: {"frequencia": 1, "primeira_posicao": 0},}

    def test_calcula_media_e_desvio_padrao_para_multiplos_documentos(self, tmp_path):
        (tmp_path / "business").mkdir()
        (tmp_path / "sport").mkdir()
        (tmp_path / "business" / "001.txt").write_text("trade trade market", encoding="latin-1")
        (tmp_path / "sport" / "002.txt").write_text("market", encoding="latin-1")
        corpus = Corpus()
        
        corpus.construir_indice(str(tmp_path))
        
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

    def test_remove_pontuacao_nas_bordas_e_ignora_pontuacao_isolada_ou_repetida(self, tmp_path):
        (tmp_path / "entertainment").mkdir()
        (tmp_path / "entertainment" / "001.txt").write_text("cinema, ... !! ? filme;", encoding="latin-1")
        corpus = Corpus()

        corpus.construir_indice(str(tmp_path))

        assert set(corpus.estatisticas_corpus.keys()) == {"cinema", "filme"}

    def test_nao_indexa_nada_quando_corpus_esta_vazio(self, tmp_path):
        corpus = Corpus()
        corpus.construir_indice(str(tmp_path))

        assert corpus.todos_documentos == set()
        assert corpus.estatisticas_corpus == {}

class TestParseLinhaTrie:
    def test_extrai_valor_e_multiplas_ocorrencias_de_linha_valida(self):
        corpus = Corpus()
        linha = (
            "  ('market',{(1, 23):{'frequencia':3, 'primeira_posicao':10}, "
            "(4, 5):{'frequencia':1, 'primeira_posicao':0}})\n"
        )

        valor, lista_invertida = corpus.parse_linha_trie(linha)

        assert valor == "market"
        assert lista_invertida == {(1, 23): {"frequencia": 3, "primeira_posicao": 10}, (4, 5): {"frequencia": 1, "primeira_posicao": 0},}

    def test_remove_caracteres_escapados_do_valor_do_no(self):
        corpus = Corpus()
        linha = r"('it\'s\:a\,b\(c\)\\',{})"
        valor, lista_invertida = corpus.parse_linha_trie(linha)

        assert valor == "it's:a,b(c)\\"
        assert lista_invertida == {}

    @pytest.mark.parametrize("linha_vazia", ["('',{})", "(,'{}')"])
    def test_retorna_valor_e_dicionario_vazios_para_representacoes_de_no_vazio(self, linha_vazia):
        corpus = Corpus()

        valor, lista_invertida = corpus.parse_linha_trie(linha_vazia)

        assert valor == ""
        assert lista_invertida == {}
        
    def test_lanca_value_error_para_linha_mal_formatada(self):
        corpus = Corpus()

        with pytest.raises(ValueError):
            corpus.parse_linha_trie("linha_sem_formato_valido")
            
class TestSalvarEmDisco:
    def test_cria_arquivo_de_indice_com_secoes_de_estatisticas_e_trie(self, tmp_path):
        corpus_dir = tmp_path / "corpus"
        (corpus_dir / "business").mkdir(parents=True)
        (corpus_dir / "business" / "001.txt").write_text("profit", encoding="latin-1")
        arquivo_saida = tmp_path / "indice.dat"
        corpus = Corpus()
        corpus.construir_indice(str(corpus_dir))
        corpus.salvar_em_disco(str(arquivo_saida))
        
        assert arquivo_saida.exists()
        conteudo = arquivo_saida.read_text(encoding="utf-8")
        assert "---ESTATISTICAS---" in conteudo
        assert "---TRIE---" in conteudo
        assert "profit" in conteudo

    def test_nao_interrompe_execucao_e_registra_erro_quando_caminho_de_saida_e_invalido(self, tmp_path, capsys):
        corpus = Corpus()
        caminho_diretorio = tmp_path / "pasta_existente"
        caminho_diretorio.mkdir()
        
        corpus.salvar_em_disco(str(caminho_diretorio))
        saida = capsys.readouterr().out
        assert "Erro ao salvar o índice" in saida
        assert caminho_diretorio.is_dir()

class TestCarregarDeDisco:
    def test_restaura_estatisticas_e_trie_salvas_incluindo_termos_com_caracteres_especiais(self, tmp_path):
        corpus_dir = tmp_path / "corpus"
        (corpus_dir / "tech").mkdir(parents=True)
        (corpus_dir / "tech" / "001.txt").write_text("it's c:d data", encoding="latin-1")
        arquivo_indice = tmp_path / "indice.dat"

        corpus_original = Corpus()
        corpus_original.construir_indice(str(corpus_dir))
        corpus_original.salvar_em_disco(str(arquivo_indice))

        corpus_carregado = Corpus()
        sucesso = corpus_carregado.carregar_de_disco(str(arquivo_indice))
        
        assert sucesso is True
        assert corpus_carregado.estatisticas_corpus == corpus_original.estatisticas_corpus
        assert corpus_carregado.trie.busca_palavra("it's") == {(Categoria.tech.value, 1): {"frequencia": 1, "primeira_posicao": 0}}
        assert corpus_carregado.trie.busca_palavra("data") == {(Categoria.tech.value, 1): {"frequencia": 1, "primeira_posicao": 9}}

    def test_retorna_false_quando_arquivo_nao_existe(self, tmp_path):
        corpus = Corpus()
        sucesso = corpus.carregar_de_disco(str(tmp_path / "nao_existe.dat"))

        assert sucesso is False
        
    def test_retorna_false_quando_arquivo_nao_possui_delimitadores_obrigatorios(self, tmp_path):
        arquivo_invalido = tmp_path / "invalido.dat"
        arquivo_invalido.write_text("conteudo qualquer sem cabecalhos\n", encoding="utf-8")
        corpus = Corpus()

        sucesso = corpus.carregar_de_disco(str(arquivo_invalido))

        assert sucesso is False

    def test_ignora_linhas_malformadas_e_carrega_registros_validos(self, tmp_path):
        arquivo = tmp_path / "parcial.dat"
        arquivo.write_text(
            "---ESTATISTICAS---\n"
            "valido:1.5,0.5\n"
            "invalido_sem_dois_pontos\n"
            "invalido_float:abc,1.0\n"
            "---TRIE---\n"
            "('',{})\n"
            "  ('valido',{(1, 1):{'frequencia':1, 'primeira_posicao':0}})\n"
            "  linha_quebrada_na_trie\n",
            encoding="utf-8",
        )
        corpus = Corpus()
        sucesso = corpus.carregar_de_disco(str(arquivo))

        assert sucesso is True
        assert corpus.estatisticas_corpus == {"valido": {"media": 1.5, "desvio_padrao": 0.5}}
        assert corpus.trie.busca_palavra("valido") == {(1, 1): {"frequencia": 1, "primeira_posicao": 0}}
