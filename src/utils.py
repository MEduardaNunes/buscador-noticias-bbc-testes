import re

def normaliza_query(query : str):
    """
    Normaliza a query, convertando palavras para minúsculo (com exceção os operadores)

    Parâmetros:
        query (str): A string a ser processada.

    Retorno:
        A string normalizada.
    """
    if not isinstance(query, str):
        raise TypeError(f"Query deve ser str, mas recebeu {type(query).__name__}")

    query_normalizada = ""
    termos_query = query.replace('(', ' ( ').replace(')', ' ) ').split()
    
    for palavra in termos_query:
        if palavra in ("AND", "OR", "NOT", "(", ")"):
            query_normalizada += palavra + " "
        else:
            query_normalizada += palavra.lower() + " "

    return query_normalizada.strip()

def _obter_caracteres_internos_palavra():
    """ Define o set de caracteres internos permitidos."""
    return frozenset(["'","^","<","|", ">", "~", "_","-","+", "=", "*", ".", ":", ",", ";", "$", "%", "£", "/", "\\", "#"]) 

def _obter_simbolos_indexaveis():
    """ Define símbolos que podem ser indexados como tokens separados."""
    return frozenset(["&","^","|",">", "<", "~", "%", ".", "=","+", "-", ":", "!", "?", "/", "\\", "#", "@", "[", "]", "{", "}"])
    
def processar_texto(texto):
    """
    Normaliza um texto: converte para minúsculas, e extrai o índice do caractere inicial de cada um no texto original.

    Parâmetros:
        texto (str): A string de entrada a ser processada.

    Retorno:
        list[tuple[str, int]]: Uma lista de tuplas, onde cada tupla contém o termo 
        normalizado (str) e seu índice de caractere inicial (int) no texto original.
        Ex: [('palavra1', 0), ('123', 9), ...]
    """
    
    tokens_com_posicao = [] # Lista para armazenar as tuplas (termo, indice_char)
    
    # Constrói o padrão para símbolos (ex: [.&%$])
    simbolos_padrao = "([%s])" % re.escape("".join(_obter_simbolos_indexaveis()))
    
    # Constrói o padrão para caracteres internos (ex: '-)
    caracteres_palavra = re.escape("".join(_obter_caracteres_internos_palavra()))
    
    padrao_palavras = r"([a-z0-9" + caracteres_palavra + r"]*[a-z0-9][a-z0-9" + caracteres_palavra + r"]*)"
    
    padrao = re.compile(
        padrao_palavras + r"|" + simbolos_padrao, 
        re.IGNORECASE
    )
    
    for match in padrao.finditer(texto):
        token = match.group(0) # Pega o texto completo do match
        indice_char = match.start() # Pega o índice inicial

        # Normaliza para minúsculas
        token_normalizado = token.lower()
        
        # Adiciona à lista
        tokens_com_posicao.append((token_normalizado, indice_char))

    return tokens_com_posicao