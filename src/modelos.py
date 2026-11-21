from enum import Enum

class Categoria(Enum):
    """
    Enumeração das categorias de documentos no corpus.
    Cada valor representa uma categoria específica de conteúdo.
    """
    business = 1
    entertainment = 2
    politics = 3
    sport = 4
    tech = 5    

class Documento:
    """Representa um documento do corpus, contendo seus metadados e conteúdo."""
    def __init__(self, categoria, doc_id, conteudo):
        """
        Parâmetros:
            categoria (str): O nome da categoria do documento (ex: 'business').
            doc_id (str): O identificador numérico do documento (ex: '001').
            conteudo (str): O texto completo do documento.
        """
        self.categoria = categoria
        self.doc_id = doc_id
        self.conteudo = conteudo
    
    def __repr__(self):
        return f"Documento(id={self.doc_id}, categoria='{self.categoria}')"
