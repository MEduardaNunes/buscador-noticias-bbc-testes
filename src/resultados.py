from src.models import Categoria
from collections import namedtuple
from src.utils import processar_texto, mergesort
from src.snippet import _gerar_snippet_formatado

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

    def adicionar_resultado(self, doc_id, relevancia, query_termo, caractere_inicial):
        """Adiciona um resultado"""
        if relevancia is None or doc_id is None:
            print(f"[Aviso GerenciadorResultados] Tentativa de adicionar resultado inválido: {doc_id}, {relevancia}")
            return
        
        item = ResultadoItem(doc_id, relevancia, query_termo, caractere_inicial)
        self._resultados.append(item)
        
    def obter_relevancia(self, item):
        """Função para obter a relevância de um ResultadoItem."""
        return item.relevancia

    def ordenar(self):
        """
        Ordena os resultados por relevância (decrescente) usando mergesort.
        
        Retorno: None
        """
        if self._resultados_ordenados is None:
            self._resultados_ordenados = mergesort(self._resultados, self.obter_relevancia)

     def gerar_snippet(self, item):
        """Tenta gerar o snippet e retorna uma mensagem em caso de falha"""
        try:
            snippet = _gerar_snippet_formatado(
                item.doc_id, 
                item.query_termo, 
                item.caractere_inicial, 
                self._caminho_corpus, 
                self._mapa_categorias,
                self._todos_os_termos
            )
            return snippet
        except Exception as e:
            print(f"[Erro GerenciadorResultados] Falha ao gerar snippet para {item.doc_id}: {e}")
            return "[Falha na geração do snippet]"

     def obter_pagina_formatada(self, num_pagina=1, tamanho_pagina=10):
        """
        Retorna uma lista de dicionários formatados para a página especificada,
        incluindo o snippet gerado. Garante que os resultados estejam ordenados.
        
        Parâmetros:
            num_pagina (int): Número da página a ser retornada (padrão é 1).
            tamanho_pagina (int): Quantidade de resultados por página (padrão é 10).

        Retorno:
            List[Dict[str, str]]: Lista de dicionários contendo os resultados da página com as informações
            formatadas, incluindo o snippet.
        """
        if self._resultados_ordenados is None:
            self.ordenar()
        
        # Calcula os índices para a paginação
        inicio = (num_pagina - 1) * tamanho_pagina
        fim = inicio + tamanho_pagina
        
        resultados_pagina = self._resultados_ordenados[inicio:fim]
        resultados_finais = []
        
        for item in resultados_pagina:
            snippet = "[Snippet não gerado]"
            
            snippet = self.gerar_snippet(item)
                
            # Formata o id do doc de (int, int) para string
            categoria_int, numero_int = item.doc_id
            categoria_nome = self._mapa_categorias.get(categoria_int, 'desconhecida')
            doc_num_str = f"{numero_int:03d}"
            doc_id_completo_str = f"{categoria_nome}/{doc_num_str}"

            resultados_finais.append({
                'id_completo': doc_id_completo_str,
                'categoria': categoria_nome,
                'id_num': doc_num_str,
                'score': f"{item.relevancia:.4f}",
                'snippet': snippet
            })
        
        return resultados_finais
