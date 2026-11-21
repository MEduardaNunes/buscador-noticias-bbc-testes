import sqlite3
from datetime import datetime, timezone

import pytest

from src.artigos_salvos import (
    RepositorioArtigosSalvosSQLite,
    ServicoArtigosSalvos,
)

class RepositorioArtigosSalvosFake:
    """Fake em memória que preserva o contrato de RepositorioArtigosSalvos."""

    def __init__(self) -> None:
        self._registros: list[dict] = []

    def salvar(self, usuario: str, categoria: str, doc_id: str, salvo_em: str) -> bool:
        if self.existe(usuario, categoria, doc_id):
            return False
        self._registros.append(
            {
                "usuario": usuario,
                "categoria": categoria,
                "doc_id": doc_id,
                "id_completo": f"{categoria}/{doc_id}",
                "salvo_em": salvo_em,
            }
        )
        return True

    def remover(self, usuario: str, categoria: str, doc_id: str) -> bool:
        for i, reg in enumerate(self._registros):
            if (
                reg["usuario"] == usuario
                and reg["categoria"] == categoria
                and reg["doc_id"] == doc_id
            ):
                self._registros.pop(i)
                return True
        return False

    def listar_por_usuario(self, usuario: str) -> list[dict]:
        return [
            {
                "categoria": r["categoria"],
                "doc_id": r["doc_id"],
                "id_completo": r["id_completo"],
                "salvo_em": r["salvo_em"],
            }
            for r in reversed(self._registros)
            if r["usuario"] == usuario
        ]

    def existe(self, usuario: str, categoria: str, doc_id: str) -> bool:
        return any(
            r["usuario"] == usuario
            and r["categoria"] == categoria
            and r["doc_id"] == doc_id
            for r in self._registros
        )
        
class TestServicoArtigosSalvos:
    def test_salvar_artigo_normaliza_dados_e_registra_timestamp(self):
        repo = RepositorioArtigosSalvosFake()
        instante_fixo = datetime(2026, 11, 21, 12, 0, 0, tzinfo=timezone.utc)
        servico = ServicoArtigosSalvos(repositorio=repo, relogio=lambda: instante_fixo)

        inserido = servico.salvar_artigo("  ana  ", " TECH ", " 042 ")

        assert inserido is True
        assert servico.listar_artigos("ana") == [
            {
                "categoria": "tech",
                "doc_id": "042",
                "id_completo": "tech/042",
                "salvo_em": "2026-11-21T12:00:00+00:00",
            }
        ]
    def test_salvar_artigo_duplicado_retorna_false(self):
        repo = RepositorioArtigosSalvosFake()
        instante_fixo = datetime(2026, 11, 21, 12, 0, 0, tzinfo=timezone.utc)
        servico = ServicoArtigosSalvos(repositorio=repo, relogio=lambda: instante_fixo)
        servico.salvar_artigo("ana", "sport", "001")

        inserido_novamente = servico.salvar_artigo("ana", "SPORT", "001")

        assert inserido_novamente is False
        assert len(servico.listar_artigos("ana")) == 1

    def test_remover_artigo_existente_retorna_true_e_remove_registro(self):
        repo = RepositorioArtigosSalvosFake()
        servico = ServicoArtigosSalvos(repositorio=repo)
        servico.salvar_artigo("ana", "business", "010")
        
        removido = servico.remover_artigo("ana", "business", "010")

        assert removido is True
        assert servico.artigo_esta_salvo("ana", "business", "010") is False

    def test_remover_artigo_inexistente_retorna_false(self):
        repo = RepositorioArtigosSalvosFake()
        servico = ServicoArtigosSalvos(repositorio=repo)

        removido = servico.remover_artigo("ana", "politics", "999")

        assert removido is False

    def test_listar_artigos_retorna_apenas_artigos_do_usuario(self):
        repo = RepositorioArtigosSalvosFake()
        servico = ServicoArtigosSalvos(repositorio=repo)
        servico.salvar_artigo("ana", "tech", "001")
        servico.salvar_artigo("bruno", "sport", "002")

        artigos_ana = servico.listar_artigos("  ana  ")

        assert len(artigos_ana) == 1
        assert artigos_ana[0]["id_completo"] == "tech/001"
        
    def test_artigo_esta_salvo_reflete_estado_atual(self):
        repo = RepositorioArtigosSalvosFake()
        servico = ServicoArtigosSalvos(repositorio=repo)
        servico.salvar_artigo("ana", "entertainment", "007")

        assert servico.artigo_esta_salvo("ana", "entertainment", "007") is True
        assert servico.artigo_esta_salvo("ana", "entertainment", "008") is False

    @pytest.mark.parametrize(
        "usuario,categoria,doc_id,mensagem_esperada",
        [
            ("", "tech", "001", "Usuário é obrigatório."),
            ("   ", "tech", "001", "Usuário é obrigatório."),
            (None, "tech", "001", "Usuário é obrigatório."),
            ("ana", "", "001", "Categoria inválida"),
            ("ana", "ciencia", "001", "Categoria inválida"),
            ("ana", "tech", "", "Identificador de documento inválido"),
            ("ana", "tech", "abc", "Identificador de documento inválido"),
            ("ana", "tech", "-1", "Identificador de documento inválido"),
        ],
    )
