from datetime import datetime, timezone
from typing import Callable, Protocol

from src.models import Categoria

class RepositorioArtigosSalvosSQLite:
    """Implementação concreta de persistência em SQLite."""

    def __init__(self, conexao_factory: Callable):
        self._conexao_factory = conexao_factory

    def inicializar_tabela(self) -> None:
        with self._conexao_factory() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS artigos_salvos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    salvo_em TEXT NOT NULL,
                    UNIQUE(usuario, categoria, doc_id)
                )
                """
            )
