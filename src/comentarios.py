"""Comentários dos usuários nos documentos do corpus."""
from datetime import datetime, timezone
from typing import Callable, Protocol

from src.modelos import Categoria

TAMANHO_MAXIMO_COMENTARIO = 500


class ComentarioNaoEncontradoError(LookupError):
    """Lançada quando o comentário solicitado não existe."""


class PermissaoNegadaError(Exception):
    """Lançada quando um usuário tenta excluir um comentário de outra pessoa."""


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

    def remover_por_usuario(self, usuario: str) -> int:
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

    @staticmethod
    def _para_dict(registro) -> dict:
        return {
            "id": registro["id"],
            "usuario": registro["usuario"],
            "categoria": registro["categoria"],
            "doc_id": registro["doc_id"],
            "texto": registro["texto"],
            "criado_em": registro["criado_em"],
        }

    def listar_por_documento(self, categoria: str, doc_id: str) -> list[dict]:
        with self._conexao_factory() as conexao:
            registros = conexao.execute(
                """
                SELECT id, usuario, categoria, doc_id, texto, criado_em
                FROM comentarios
                WHERE categoria = ? AND doc_id = ?
                ORDER BY id ASC
                """,
                (categoria, doc_id),
            ).fetchall()

        return [self._para_dict(r) for r in registros]

    def buscar_por_id(self, comentario_id: int) -> dict | None:
        with self._conexao_factory() as conexao:
            registro = conexao.execute(
                """
                SELECT id, usuario, categoria, doc_id, texto, criado_em
                FROM comentarios
                WHERE id = ?
                """,
                (comentario_id,),
            ).fetchone()

        return self._para_dict(registro) if registro is not None else None

    def remover(self, comentario_id: int) -> bool:
        with self._conexao_factory() as conexao:
            cursor = conexao.execute(
                "DELETE FROM comentarios WHERE id = ?",
                (comentario_id,),
            )
            return cursor.rowcount > 0

    def remover_por_usuario(self, usuario: str) -> int:
        with self._conexao_factory() as conexao:
            cursor = conexao.execute(
                "DELETE FROM comentarios WHERE usuario = ?",
                (usuario,),
            )
            return cursor.rowcount


class ServicoComentarios:
    """Regras de negócio dos comentários: validação, publicação, listagem e exclusão."""

    def __init__(
        self,
        repositorio: RepositorioComentarios,
        relogio: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._repositorio = repositorio
        self._relogio = relogio

    @staticmethod
    def _validar_usuario(usuario: str) -> str:
        usuario_limpo = (usuario or "").strip()
        if not usuario_limpo:
            raise ValueError("Usuário é obrigatório.")
        return usuario_limpo

    @staticmethod
    def _validar_documento(categoria: str, doc_id: str) -> tuple[str, str]:
        categoria_limpa = (categoria or "").strip().lower()
        doc_id_limpo = (doc_id or "").strip()

        if categoria_limpa not in {c.name for c in Categoria}:
            raise ValueError(f"Categoria inválida: '{categoria}'.")

        if not doc_id_limpo.isdigit():
            raise ValueError(f"Identificador de documento inválido: '{doc_id}'.")

        # Normaliza o identificador para 3 dígitos, como nos arquivos do corpus (ex: '7' -> '007')
        return categoria_limpa, f"{int(doc_id_limpo):03d}"

    @staticmethod
    def _validar_texto(texto: str) -> str:
        texto_limpo = (texto or "").strip()
        if not texto_limpo:
            raise ValueError("O comentário não pode estar vazio.")
        if len(texto_limpo) > TAMANHO_MAXIMO_COMENTARIO:
            raise ValueError(f"O comentário deve ter no máximo {TAMANHO_MAXIMO_COMENTARIO} caracteres.")
        return texto_limpo

    def comentar(self, usuario: str, categoria: str, doc_id: str, texto: str) -> int:
        """Publica um comentário no documento. Retorna o identificador do comentário criado."""
        usuario_limpo = self._validar_usuario(usuario)
        categoria_limpa, doc_id_limpo = self._validar_documento(categoria, doc_id)
        texto_limpo = self._validar_texto(texto)
        criado_em = self._relogio().isoformat()
        return self._repositorio.adicionar(usuario_limpo, categoria_limpa, doc_id_limpo, texto_limpo, criado_em)

    def listar_comentarios(self, categoria: str, doc_id: str) -> list[dict]:
        """Lista os comentários do documento em ordem de publicação, com a data formatada para exibição."""
        categoria_limpa, doc_id_limpo = self._validar_documento(categoria, doc_id)
        comentarios = self._repositorio.listar_por_documento(categoria_limpa, doc_id_limpo)
        return [
            {**comentario, "data_exibicao": datetime.fromisoformat(comentario["criado_em"]).strftime("%d/%m/%Y %H:%M")}
            for comentario in comentarios
        ]

    def excluir_comentario(self, usuario: str, comentario_id: int) -> dict:
        """
        Exclui um comentário, desde que o usuário seja o autor.
        Retorna o comentário excluído (útil para redirecionar ao documento).
        """
        usuario_limpo = self._validar_usuario(usuario)
        comentario = self._repositorio.buscar_por_id(comentario_id)

        if comentario is None:
            raise ComentarioNaoEncontradoError(f"Comentário {comentario_id} não encontrado.")

        if comentario["usuario"] != usuario_limpo:
            raise PermissaoNegadaError("Apenas o autor pode excluir o comentário.")

        self._repositorio.remover(comentario_id)
        return comentario

    def excluir_comentarios_do_usuario(self, usuario: str) -> int:
        """Exclui todos os comentários do usuário (usado ao excluir a conta). Retorna quantos foram removidos."""
        usuario_limpo = self._validar_usuario(usuario)
        return self._repositorio.remover_por_usuario(usuario_limpo)
