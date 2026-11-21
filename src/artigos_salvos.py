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
            
    def salvar(self, usuario: str, categoria: str, doc_id: str, salvo_em: str) -> bool:
        with self._conexao_factory() as conexao:
            cursor = conexao.execute(
                """
                INSERT OR IGNORE INTO artigos_salvos (usuario, categoria, doc_id, salvo_em)
                VALUES (?, ?, ?, ?)
                """,
                (usuario, categoria, doc_id, salvo_em),
            )
            return cursor.rowcount > 0

    def remover(self, usuario: str, categoria: str, doc_id: str) -> bool:
        with self._conexao_factory() as conexao:
            cursor = conexao.execute(
                """
                DELETE FROM artigos_salvos
                WHERE usuario = ? AND categoria = ? AND doc_id = ?
                """,
                (usuario, categoria, doc_id),
            )
            return cursor.rowcount > 0
            
    def listar_por_usuario(self, usuario: str) -> list[dict]:
        with self._conexao_factory() as conexao:
            registros = conexao.execute(
                """
                SELECT categoria, doc_id, salvo_em
                FROM artigos_salvos
                WHERE usuario = ?
                ORDER BY id DESC
                """,
                (usuario,),
            ).fetchall()

        return [
            {
                "categoria": r["categoria"],
                "doc_id": r["doc_id"],
                "id_completo": f"{r['categoria']}/{r['doc_id']}",
                "salvo_em": r["salvo_em"],
            }
            for r in registros
        ]
        
    def existe(self, usuario: str, categoria: str, doc_id: str) -> bool:
        with self._conexao_factory() as conexao:
            registro = conexao.execute(
                """
                SELECT 1 FROM artigos_salvos
                WHERE usuario = ? AND categoria = ? AND doc_id = ?
                """,
                (usuario, categoria, doc_id),
            ).fetchone()
        return registro is not None
        
class ServicoArtigosSalvos:
    def __init__(
        self,
        repositorio: RepositorioArtigosSalvos,
        relogio: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._repositorio = repositorio
        self._relogio = relogio

    @staticmethod
    def _validar_identificadores(usuario: str, categoria: str, doc_id: str) -> tuple[str, str, str]:
        usuario_limpo = (usuario or "").strip()
        categoria_limpa = (categoria or "").strip().lower()
        doc_id_limpo = (doc_id or "").strip()

        if not usuario_limpo:
            raise ValueError("Usuário é obrigatório.")

        categorias_validas = {c.name for c in Categoria}
        if categoria_limpa not in categorias_validas:
            raise ValueError(f"Categoria inválida: '{categoria}'.")

        if not doc_id_limpo or not doc_id_limpo.isdigit():
            raise ValueError(f"Identificador de documento inválido: '{doc_id}'.")

        return usuario_limpo, categoria_limpa, doc_id_limpo

    def salvar_artigo(self, usuario: str, categoria: str, doc_id: str) -> bool:
        """Salva um artigo para o usuário. Retorna True se inserido, False se já existia."""
        u, cat, did = self._validar_identificadores(usuario, categoria, doc_id)
        salvo_em = self._relogio().isoformat()
        return self._repositorio.salvar(u, cat, did, salvo_em)

    def remover_artigo(self, usuario: str, categoria: str, doc_id: str) -> bool:
        """Remove um artigo salvo. Retorna True se removido, False se não existia."""
        u, cat, did = self._validar_identificadores(usuario, categoria, doc_id)
        return self._repositorio.remover(u, cat, did)

    def listar_artigos(self, usuario: str) -> list[dict]:
        """Lista todos os artigos salvos pelo usuário."""
        usuario_limpo = (usuario or "").strip()
        if not usuario_limpo:
            raise ValueError("Usuário é obrigatório.")
        return self._repositorio.listar_por_usuario(usuario_limpo)

    def artigo_esta_salvo(self, usuario: str, categoria: str, doc_id: str) -> bool:
        """Verifica se um artigo específico está salvo pelo usuário."""
        u, cat, did = self._validar_identificadores(usuario, categoria, doc_id)
        return self._repositorio.existe(u, cat, did)
