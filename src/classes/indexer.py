from TrieCompacta import TrieCompacta, NoTrie
from .utils import processar_texto
from .models import Documento, Categoria
import os
import math
import re

def ler_documentos(caminho_corpus):
        documentos = []
        
        for categoria in os.listdir(caminho_corpus):
            caminho_categoria = os.path.join(caminho_corpus, categoria)
            
            if os.path.isdir(caminho_categoria):
                for nome_arquivo in os.listdir(caminho_categoria):
                    if nome_arquivo.endswith('.txt'):
                        doc_id_num = nome_arquivo[:-4]
                        caminho_arquivo = os.path.join(caminho_categoria, nome_arquivo)
                        
                        try:
                            with open(caminho_arquivo, 'r', encoding='latin-1') as f:
                                conteudo = f.read()
                            doc = Documento(categoria, doc_id_num, conteudo)
                            documentos.append(doc)
                        except Exception as e:
                            print(f"Erro ao ler o arquivo {caminho_arquivo}: {e}")
        
        return documentos

class Corpus:
    def __init__(self):
            """Inicializa um objeto com uma trie vazia e um dicionário de estatísticas vazio"""
            self.trie = TrieCompacta()
            self.estatisticas_corpus = {}  # Formato: {"termo": {"media": x, "desvio_padrao": y}}  
            self.todos_documentos = set()

    def _processar_documentos(self, documentos):
        """
        Processa uma lista de documentos, preenchendo a Trie e o set 'todos_documentos'.
        Retorna os dicionários de frequência necessários para as estatísticas.
        """
        # Dicionário temporário para calcular frequências
        frequencias_por_doc = {} # Formato: {'business/001': {'trade': 5, 'market': 3}, ...}
                
        for doc in documentos:
            doc_id_completo = f"{doc.categoria}/{doc.doc_id}" # Cria um id único para cada doc (ex: 'business/001')
            frequencias_por_doc[doc_id_completo] = {}
            
            # Converte os identificadores do doc para inteiros
            categoria_int = Categoria[doc.categoria].value
            numero_int = int(doc.doc_id) 
            doc_id_tupla = (categoria_int, numero_int)
            self.todos_documentos.add(doc_id_tupla)

            # Normalização do texto
            termos_com_posicao = processar_texto(doc.conteudo)
            
            for termo, indice_char in termos_com_posicao:
                
                # Pula pontuações repetidas (ex: "!!", "...")
                if re.fullmatch(r"([.,!?;:])\1+", termo):
                    continue 
                else:
                    # Remove pontuação do início ou fim do termo
                    termo = re.sub(r"^[,.!?;:]+|[,.!?;:]+$", "", termo)
                    
                if not termo: # Pula o termo se ele ficou vazio (ex: era só um ".")
                    continue
                
                # Preenche o dicionário de frequências do doc atual
                frequencias_por_doc[doc_id_completo][termo] = frequencias_por_doc[doc_id_completo].get(termo, 0) + 1
                
                # Insere o termo, o id do documento e a primeira posição de ocorrência do termo na trie compacta
                self.trie.insere_palavra(termo, doc_id_tupla, indice_char)
        
        # Cria o set de todos os termos únicos encontrados
        todos_os_termos = set(termo for freqs in frequencias_por_doc.values() for termo in freqs)
        
        return frequencias_por_doc, todos_os_termos
            
    def construir_indice(self, caminho_corpus):
        """
        Método responsável por fazer o processo de indexação.
        
        Parâmetros:
            caminho_corpus (str): O caminho para o diretório raiz do corpus de documentos
        """
        self.todos_documentos.clear()
        
        documentos = ler_documentos(caminho_corpus)
        total_docs = len(documentos)
        
        if total_docs == 0:
            print("[CONSTRUIR_INDICE] A lista de documentos está vazia. A indexação não pode continuar.")
            return
        
        # Formato frequencias_por_doc: {'business/001': {'trade': 5, 'market': 3}, ...}
        # Formato lista_de_frequencias_por_termo: {'trade': [5, 0, 2, ...], 'market': [3, 1, 0, ...]}
        
        # Processa os documentos, preenche a Trie e calcula as frequências
        frequencias_por_doc, todos_os_termos = self._processar_documentos(documentos)
        
        # Transforma os dados para uma lista de freqs por termo
        lista_de_frequencias_por_termo = self._construir_lista_frequencias(todos_os_termos, frequencias_por_doc)
        
        # Calcula média e desvio padrão para cada termo
        self._calcular_estatisticas(total_docs, lista_de_frequencias_por_termo)
            
    def _construir_lista_frequencias(self, todos_os_termos, frequencias_por_doc):
        """
        Converte o dicionário 'frequencias_por_doc' em um dicionário 
        de 'termo -> [lista de frequências]', necessário para o cálculo estatístico.
        """
        lista_de_frequencias_por_termo = {}
        
        for termo in todos_os_termos:
            lista_de_frequencias_por_termo[termo] = []
            # Para cada documento, pega a frequência daquele termo
            for doc_id in frequencias_por_doc:
                freq = frequencias_por_doc[doc_id].get(termo, 0)
                lista_de_frequencias_por_termo[termo].append(freq)
                
        return lista_de_frequencias_por_termo

    def _calcular_estatisticas(self, total_docs, lista_de_frequencias_por_termo):
        """Calcula estatísticas de frequência (média, desvio padrão) para cada termo"""
        
        for termo, freqs in lista_de_frequencias_por_termo.items():
            soma_freq = sum(freqs)
            media = soma_freq / total_docs
            
            if total_docs > 1:
                variancia = 0
                soma_das_diferencas_quadradas = 0 
                
                for freq in freqs:
                    soma_das_diferencas_quadradas += (freq - media) ** 2
                
                variancia = soma_das_diferencas_quadradas / (total_docs - 1)
                desvio_padrao = math.sqrt(variancia)
            else:
                # Evita divisão por zero se houver apenas 1 documento
                desvio_padrao = 0
                
            self.estatisticas_corpus[termo] = {"media": media, "desvio_padrao": desvio_padrao}
