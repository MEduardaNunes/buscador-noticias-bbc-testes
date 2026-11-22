"""Comentários dos usuários nos documentos do corpus."""
from typing import Protocol


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
