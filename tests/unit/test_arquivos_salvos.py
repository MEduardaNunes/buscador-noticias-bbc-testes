import sqlite3
from datetime import datetime, timezone

import pytest

from src.arquivos_salvos import (
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
