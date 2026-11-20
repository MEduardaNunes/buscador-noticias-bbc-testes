from modules.models import Categoria
from collections import namedtuple
from modules.utils import processar_texto, mergesort
from modules.snippet import _gerar_snippet_formatado

ResultadoItem = namedtuple('ResultadoItem', [
    'doc_id', # tupla (cat_int, num_int)
    'relevancia', # float (média dos z-scores)
    'query_termo', # str (o termo da query a ser destacado)
    'caractere_inicial' # int (índice do caractere inicial do query_termo)
])

class GerenciadorResultados:
    """Armazena os resultados de uma busca, ordena-os por relevância e fornece snippets formatados"""
    def __init__(self, caminho_corpus, mapa_categorias, todos_os_termos: list):
        self._resultados= [] # Lista de ResultadoItem
        self._resultados_ordenados = None # Lista de resultados ordenados
        self._caminho_corpus = caminho_corpus
        self._mapa_categorias = mapa_categorias
        self._todos_os_termos = todos_os_termos
