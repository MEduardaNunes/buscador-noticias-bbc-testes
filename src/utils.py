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