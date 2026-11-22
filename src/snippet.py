"""Geração de snippets (trechos destacados) dos documentos retornados por uma busca."""
import os
import re


def _ler_conteudo_documento(doc_id, caminho_corpus, mapa_categorias):
    """
    Lê o conteúdo de um documento específico a partir do caminho fornecido.

    Parâmetros:
    - doc_id (tuple): Tupla contendo a categoria numérica e o número do documento (categoria_id, numero_id).
    - caminho_corpus (str): Caminho raiz onde os arquivos de documentos estão armazenados.
    - mapa_categorias (dict): Dicionário que mapeia os valores int de categoria para seus respectivos nomes.

    Retorna:
    - str: O conteúdo do arquivo de texto do documento ou None se o arquivo não for encontrado ou ocorrer um erro.
    """
    caminho_arquivo = None

    try:
        # Converte id do documento em caminho de arquivo (Ex: 1, 003 -> business/003.txt)
        categoria_int, numero_int = doc_id
        categoria_nome = mapa_categorias.get(categoria_int)
        if not categoria_nome:
            return None
        nome_arquivo = f"{numero_int:03d}.txt"
        caminho_arquivo = os.path.join(caminho_corpus, categoria_nome, nome_arquivo)
        with open(caminho_arquivo, 'r', encoding='latin-1') as f:
            return f.read()
    except (FileNotFoundError, IOError):
        info_erro = caminho_arquivo if caminho_arquivo else str(doc_id)
        print(f"[Erro na leitura de documento para criar snippet] Arquivo não encontrado: {info_erro}")
        return None
    except Exception as e:
        info_erro = caminho_arquivo if caminho_arquivo else str(doc_id)
        print(f"[Erro na leitura de documento para criar snippet] Erro inesperado ao ler {info_erro}: {e}")
        return None
