import sqlite3
from datetime import datetime, timezone

import pytest

from src.comentarios import (
    ComentarioNaoEncontradoError,
    PermissaoNegadaError,
    RepositorioComentariosSQLite,
    ServicoComentarios,
    TAMANHO_MAXIMO_COMENTARIO,
)

INSTANTE_FIXO = datetime(2026, 11, 22, 14, 30, tzinfo=timezone.utc)


class RepositorioComentariosFake:
    """Fake em memória que preserva o contrato de RepositorioComentarios."""

    def __init__(self) -> None:
        self._comentarios: list[dict] = []
        self._proximo_id = 1

    def adicionar(self, usuario, categoria, doc_id, texto, criado_em) -> int:
        comentario = {
            "id": self._proximo_id,
            "usuario": usuario,
            "categoria": categoria,
            "doc_id": doc_id,
            "texto": texto,
            "criado_em": criado_em,
        }
        self._comentarios.append(comentario)
        self._proximo_id += 1
        return comentario["id"]

    def listar_por_documento(self, categoria, doc_id) -> list[dict]:
        return [dict(c) for c in self._comentarios if c["categoria"] == categoria and c["doc_id"] == doc_id]

    def buscar_por_id(self, comentario_id):
        return next((dict(c) for c in self._comentarios if c["id"] == comentario_id), None)

    def remover(self, comentario_id) -> bool:
        tamanho_antes = len(self._comentarios)
        self._comentarios = [c for c in self._comentarios if c["id"] != comentario_id]
        return len(self._comentarios) < tamanho_antes


@pytest.fixture
def servico():
    return ServicoComentarios(repositorio=RepositorioComentariosFake(), relogio=lambda: INSTANTE_FIXO)


class TestServicoComentarios:
    def test_comentar_registra_texto_sem_espacos_nas_bordas_com_autor_e_data(self, servico):
        servico.comentar("ana", "business", "001", "   Ótima notícia!   ")

        comentarios = servico.listar_comentarios("business", "001")

        assert len(comentarios) == 1
        assert comentarios[0]["usuario"] == "ana"
        assert comentarios[0]["texto"] == "Ótima notícia!"
        assert comentarios[0]["data_exibicao"] == "22/11/2026 14:30"

    @pytest.mark.parametrize("texto", ["", "     ", None])
    def test_rejeita_comentario_vazio(self, servico, texto):
        with pytest.raises(ValueError):
            servico.comentar("ana", "business", "001", texto)

    def test_aceita_comentario_com_tamanho_maximo(self, servico):
        texto_no_limite = "a" * TAMANHO_MAXIMO_COMENTARIO

        servico.comentar("ana", "business", "001", texto_no_limite)

        assert servico.listar_comentarios("business", "001")[0]["texto"] == texto_no_limite

    def test_rejeita_comentario_acima_do_tamanho_maximo(self, servico):
        texto_acima_do_limite = "a" * (TAMANHO_MAXIMO_COMENTARIO + 1)

        with pytest.raises(ValueError):
            servico.comentar("ana", "business", "001", texto_acima_do_limite)

    @pytest.mark.parametrize(
        ("categoria", "doc_id"),
        [("esportes", "001"), ("", "001"), ("business", "abc"), ("business", "")],
    )
    def test_rejeita_comentario_em_documento_invalido(self, servico, categoria, doc_id):
        with pytest.raises(ValueError):
            servico.comentar("ana", categoria, doc_id, "Comentário")

    @pytest.mark.parametrize("usuario", ["", "   ", None])
    def test_rejeita_comentario_sem_usuario(self, servico, usuario):
        with pytest.raises(ValueError):
            servico.comentar(usuario, "business", "001", "Comentário")

    def test_lista_apenas_comentarios_do_documento_em_ordem_de_publicacao(self, servico):
        servico.comentar("ana", "business", "001", "Primeiro")
        servico.comentar("bia", "tech", "001", "Outro documento")
        servico.comentar("duda", "business", "001", "Segundo")

        textos = [c["texto"] for c in servico.listar_comentarios("business", "001")]

        assert textos == ["Primeiro", "Segundo"]

    def test_trata_identificador_com_e_sem_zeros_a_esquerda_como_mesmo_documento(self, servico):
        servico.comentar("ana", "Business", "7", "Comentário")

        comentarios = servico.listar_comentarios("business", "007")

        assert [c["texto"] for c in comentarios] == ["Comentário"]

    def test_autor_exclui_o_proprio_comentario(self, servico):
        comentario_id = servico.comentar("ana", "business", "001", "Vou apagar")

        servico.excluir_comentario("ana", comentario_id)

        assert servico.listar_comentarios("business", "001") == []

    def test_impede_exclusao_de_comentario_de_outro_usuario(self, servico):
        comentario_id = servico.comentar("ana", "business", "001", "Comentário da Ana")

        with pytest.raises(PermissaoNegadaError):
            servico.excluir_comentario("bia", comentario_id)

        assert [c["texto"] for c in servico.listar_comentarios("business", "001")] == ["Comentário da Ana"]
