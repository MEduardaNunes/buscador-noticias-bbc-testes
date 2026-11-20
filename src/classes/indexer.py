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

