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

