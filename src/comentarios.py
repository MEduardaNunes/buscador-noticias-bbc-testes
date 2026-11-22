"""Comentários dos usuários nos documentos do corpus."""
from typing import Callable, Protocol


class RepositorioComentarios(Protocol):
    """Contrato de persistência dos comentários, permitindo substituição por Fakes em testes."""

    def adicionar(self, usuario: str, categoria: str, doc_id: str, texto: str, criado_em: str) -> int:
        ...

    def listar_por_documento(self, categoria: str, doc_id: str) -> list[dict]:
        ...

    def buscar_por_id(self, comentario_id: int) -> dict | None:
        ...

    def remover(self, comentario_id: int) -> bool:
        ...


class RepositorioComentariosSQLite:
    """Implementação concreta da persistência de comentários em SQLite."""

    def __init__(self, conexao_factory: Callable):
        self._conexao_factory = conexao_factory

    def inicializar_tabela(self) -> None:
        with self._conexao_factory() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS comentarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    texto TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                )
                """
            )

    def adicionar(self, usuario: str, categoria: str, doc_id: str, texto: str, criado_em: str) -> int:
        with self._conexao_factory() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO comentarios (usuario, categoria, doc_id, texto, criado_em)
                VALUES (?, ?, ?, ?, ?)
                """,
                (usuario, categoria, doc_id, texto, criado_em),
            )
            return cursor.lastrowid
