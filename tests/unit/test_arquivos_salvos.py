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
