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
