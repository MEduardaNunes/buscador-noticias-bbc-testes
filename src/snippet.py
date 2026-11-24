"""Geração de snippets (trechos destacados) dos documentos retornados por uma busca."""
import os
import re

from src.utilitarios import mergesort


def gerar_snippet_primeiras_frases(conteudo_documento):
    """Retorna as duas primeiras frases do primeiro parágrafo do corpo do documento."""
    paragrafos = re.split(r'\n\s*\n', conteudo_documento.strip(), maxsplit=1)
    if not paragrafos or not paragrafos[0]:
        return ""

    texto = paragrafos[1].strip() if len(paragrafos) > 1 else paragrafos[0]
    frases = re.split(r'(?<=[.!?])\s+', texto)
    return " ".join(frases[:2]).strip()


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


def _calcular_limites_snippet(tamanho_conteudo_documento, indice_caractere_inicial, len_termo):
    """
    Calcula os limites para o trecho (snippet) a ser extraído de um documento, baseado no índice do termo e seu tamanho.

    Parâmetros:
    - tamanho_conteudo_documento (int): O comprimento total do conteúdo do documento.
    - indice_caractere_inicial (int): O índice inicial onde o termo de interesse começa no conteúdo.
    - len_termo (int): O comprimento do termo de interesse.

    Retorna:
    - tuple: Um tupla contendo os índices (início, fim) do snippet, com 80 caracteres antes e depois do termo.
    """
    # Define o início do snippet 80 caracteres antes do termo (limitado a 0)
    inicio = max(0, indice_caractere_inicial - 80)

    # Define o fim do snippet 80 caracteres depois do fim do termo (limitado ao tamanho do conteúdo)
    fim = min(tamanho_conteudo_documento, indice_caractere_inicial + len_termo + 80)

    return inicio, fim


def destacar_termos_no_snippet(texto_snippet, termos_validos: list):
    """
    Destaca todos os termos válidos dentro do snippet de texto, envolvendo-os com a tag <b>.
    Evita aninhamento de tags (ex: <b><b>termo</b></b>).

    Parâmetros:
    - texto_snippet (str): O texto do snippet onde os termos válidos serão destacados.
    - termos_validos (list): Lista de termos válidos da query que precisam ser destacados.

    Retorna:
    - str: O snippet de texto com os termos destacados.
    """
    texto_modificado = texto_snippet

    # Normaliza os termos para minúsculas e remove duplicatas
    conjunto_termos = {t.lower() for t in termos_validos if t and len(t) > 0}

    # Ordena por tamanho, do maior para o menor (por exemplo, garante que "40%" seja processado antes de "%", evitando tags <b><b>)
    termos_para_destaque = mergesort(list(conjunto_termos), chave=len)

    for termo in termos_para_destaque:
        termo_escapado = re.escape(termo)

        # Adiciona \b apenas se o termo começar/terminar com um caractere alfanumérico (\w), evitando problemas com termos como "40%" ou "$"
        padrao_prefixo = r'\b' if re.match(r'^\w', termo) else r''
        padrao_sufixo = r'\b' if re.match(r'.*\w$', termo) else r''

        # O termo_escapado é usado para substituir apenas o termo preservando os limites (\b) se eles existirem
        string_padrao = padrao_prefixo + r'(' + termo_escapado + r')' + padrao_sufixo

        matches_para_substituir = []

        # Itera sobre todas as correspondências do termo no snippet
        for match in re.finditer(string_padrao, texto_modificado, flags=re.IGNORECASE):

            # Pega o texto antes da correspondência
            texto_antes = texto_modificado[:match.start()]

            # Verifica se a última tag antes do match foi <b> ou </b>
            ultima_abertura = texto_antes.rfind('<b>')
            ultimo_fechamento = texto_antes.rfind('</b>')

            # Se 'ultima_abertura > ultimo_fechamento', o match está dentro de uma tag <b>
            if ultima_abertura > ultimo_fechamento:
                continue # Pula este match pois ele já está destacado

            # Se não, é um match válido para destacar
            matches_para_substituir.append(match)

        # Aplica as substituições (do fim para o começo, para não invalidar os índices)
        for match in reversed(matches_para_substituir):
            grupo_match = match.group(1)

            inicio = match.start(1)
            fim = match.end(1)

            texto_modificado = texto_modificado[:inicio] + f"<b>{grupo_match}</b>" + texto_modificado[fim:]

    return texto_modificado


def _obter_indice_termo(conteudo_documento, termo_em_foco, indice_caractere_inicial):
    """
    Obtém o índice do termo de foco no conteúdo, utilizando o índice inicial fornecido ou buscando uma alternativa com a função find().

    Parâmetros:
    - conteudo_documento (str): O conteúdo completo do documento.
    - termo_em_foco (str): O termo que deve ser localizado no conteúdo.
    - indice_caractere_inicial (int): O índice inicial sugerido para começar a busca do termo.

    Retorna:
    - int: O índice do termo no conteúdo ou -1 caso o termo não seja encontrado.
    """
    if not (0 <= indice_caractere_inicial < len(conteudo_documento)):
        indice_alternativo = conteudo_documento.lower().find(termo_em_foco.lower())
        print(f"[Aviso Snippet] Índice {indice_caractere_inicial} inválido. Usando find() para {indice_alternativo}.")
        return indice_alternativo
    else:
        termo_no_conteudo_documento = conteudo_documento[indice_caractere_inicial : indice_caractere_inicial + len(termo_em_foco)]
        if termo_no_conteudo_documento.lower() != termo_em_foco.lower():
            indice_alternativo = conteudo_documento.lower().find(termo_em_foco.lower())
            if indice_alternativo != -1:
                return indice_alternativo
            else:
                print(f"[Aviso Snippet] Termo '{termo_em_foco}' não encontrado no conteúdo.")
                return -1  # Termo não encontrado
    return indice_caractere_inicial


def gerar_snippet_formatado(doc_id, termo_em_foco, indice_caractere_inicial, caminho_corpus, mapa_categorias, termos_validos):
    """
    Gera um snippet formatado a partir de um documento, destacando o termo de foco e todos os outros termos válidos da consulta.

    Parâmetros:
    - doc_id (tuple): Tupla contendo o id do documento (categoria_id, numero_id).
    - termo_em_foco (str): O termo da consulta que será o foco central do snippet.
    - indice_caractere_inicial (int): O índice inicial onde o termo de foco começa no conteúdo.
    - caminho_corpus (str): Caminho do diretório onde os documentos estão armazenados.
    - mapa_categorias (dict): Dicionário que mapeia categorias numéricas para seus nomes.
    - termos_validos (list): Lista de termos válidos da consulta que precisam ser destacados.

    Retorna:
    - str: O snippet formatado com os termos destacados, incluindo prefixo "..." e sufixo "..." quando necessário.
    """
    conteudo_documento = _ler_conteudo_documento(doc_id, caminho_corpus, mapa_categorias)

    if conteudo_documento is None:
        return "[Documento não encontrado]"

    indice_caractere_inicial = _obter_indice_termo(conteudo_documento, termo_em_foco, indice_caractere_inicial)

    if indice_caractere_inicial == -1:
        return "[Termo de foco não encontrado no documento]"

    # Calcula limites, extrai e destaca o termo
    tamanho_termo_em_foco = len(termo_em_foco)
    inicio_snippet, fim_snippet = _calcular_limites_snippet(len(conteudo_documento), indice_caractere_inicial, tamanho_termo_em_foco)

    texto_snippet = conteudo_documento[inicio_snippet:fim_snippet]

    snippet_destacado = destacar_termos_no_snippet(texto_snippet, termos_validos)

    prefixo = "... " if inicio_snippet > 0 else ""
    sufixo = " ..." if fim_snippet < len(conteudo_documento) else ""

    return prefixo + snippet_destacado + sufixo
