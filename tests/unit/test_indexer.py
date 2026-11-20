from src.classes.indexer import ler_documentos
import pytest

def test_ler_documentos_carrega_arquivos_txt_em_multiplas_categorias_com_latin1(tmp_path):
    cat_esportes = tmp_path / "esportes"
    cat_politica = tmp_path / "politica"
    cat_esportes.mkdir()
    cat_politica.mkdir()

    (cat_esportes / "001.txt").write_bytes("Futebol e campeão".encode("latin-1"))
    (cat_politica / "002.txt").write_bytes("Eleição municipal".encode("latin-1"))

    documentos = ler_documentos(str(tmp_path))

    resultado = {(d.categoria, d.doc_id_num, d.conteudo) for d in documentos}
    assert resultado == {
        ("esportes", "001", "Futebol e campeão"),
        ("politica", "002", "Eleição municipal"),
    }

def test_ler_documentos_retorna_lista_vazia_quando_corpus_esta_vazio(tmp_path):
    documentos = ler_documentos(str(tmp_path))

    assert documentos == []

def test_ler_documentos_ignora_arquivos_soltos_na_raiz_do_corpus(tmp_path):
    (tmp_path / "ignorado.txt").write_text("conteudo", encoding="latin-1")

    documentos = ler_documentos(str(tmp_path))
    assert documentos == []

def test_ler_documentos_ignora_arquivos_que_nao_terminam_com_txt(tmp_path):
    cat = tmp_path / "noticias"
    cat.mkdir()
    (cat / "valido.txt").write_text("ok", encoding="latin-1")
    (cat / "ignorado.csv").write_text("a,b", encoding="latin-1")
    (cat / "maiusculo.TXT").write_text("nao lido", encoding="latin-1")

    documentos = ler_documentos(str(tmp_path))

    assert len(documentos) == 1
    assert documentos[0].doc_id_num == "valido"

def test_ler_documentos_continua_leitura_quando_um_arquivo_falha(tmp_path, capsys):
    cat = tmp_path / "economia"
    cat.mkdir()
    (cat / "pasta_invalida.txt").mkdir()  # Força IsADirectoryError ao tentar open()
    (cat / "valido.txt").write_text("texto valido", encoding="latin-1")

    documentos = ler_documentos(str(tmp_path))
    saida = capsys.readouterr().out

    assert len(documentos) == 1
    assert documentos[0].doc_id_num == "valido"
    assert "Erro ao ler o arquivo" in saida


