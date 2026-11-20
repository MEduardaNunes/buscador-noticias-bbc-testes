from __future__ import annotations

class NoTrie:
    """
    Representa um nó da Trie.
    
    Atributos:
        valor (str): string contida no nó
        filhos (list[NoTrieNo]): Nós filhos desse nó.
        documentos (dict[tuple[int, int], dict[str, int]]): dicionário 
            que mapeia uma chave (seção, número) que indica o documento e 
            associa à frequência de ocorrência de uma palavra no documento
            e à primeira ocorrência dessa palavra.
    """

    def __init__(self, valor):
        self.valor = valor
        self.filhos = []
        self.documentos = {}

    def insere_filho(self, filho : NoTrie):
        """
        Insere um nó filho em ordem de leitura.
        
        Parâmetros:
            filho (NoTrie): nó filho a ser inserido.
        """
        if not isinstance(filho, NoTrie):
            raise TypeError(f"Esperado NoTrie, mas recebeu {type(filho).__name__}")
            
        self.filhos.append(filho)

    def insere_documento(self, chave : tuple[int, int], posicao_no_doc : int) -> None:
        """
        Atualiza os documentos de um nó com uma nova ocorrência.
        
        Parâmetros:
            chave (tuple[int, int]): tupla (seção, número) de um documento.
            posicao_no_doc (int): posição dentro do documento da palavra.
        """
        if not isinstance(chave, tuple) or len(chave) != 2 or not all(isinstance(x, int) for x in chave):
            raise TypeError(f"Chave deve ser do tipo tuple[int, int], recebido {type(chave)}")

        if chave[0] < 0 or chave[1] < 0:
            raise ValueError("Valores das chaves devem ser não negativos.")

        if not isinstance(posicao_no_doc, int):
            raise TypeError(f"Valor de posição esperada int, recebido {type(posicao_no_doc).__name__}")

        if posicao_no_doc < 0:
            raise ValueError("Valor da posição no documento deve se rnão negativa.")

        if chave in self.documentos:
            self.documentos[chave]["frequencia"] += 1

        else:
            self.documentos[chave] = {
                "frequencia": 1,
                "primeira_posicao": posicao_no_doc
            }


def prefixo_comum(string_um : str | None, string_dois : str | None):
    """
    Retorna o maior prefixo em comum de duas strings.
        
    Parâmetros:
        string_um (string): primeira string.
        string_dois (string): segunda string.

    Retorna:
        O prefixo em comum.
    """
    if string_um is None or string_dois is None:
        return ""

    if not isinstance(string_um, str) or not isinstance(string_dois, str):
        raise TypeError(f"Parâmetros devem ser strings ou None mas recebeu {type(string_um).__name__} e {type(string_dois).__name__}")

    i = 0
    while (i < len(string_um) and i < len(string_dois) and string_um[i] == string_dois[i]):
        i += 1

    return string_um[:i]


class TrieCompacta:
    """
    Representa uma Trie Compacta.
    
    Atributos:
        raiz (NoTrie): nó raiz da árvore.
    """

    def __init__(self):
        self.raiz = NoTrie("")

    def insere_palavra(self, palavra : str, chave : tuple[int, int], posicao : int):
        """
        Insere uma palavra na árvore trie.
            
        Parâmetros:
            palavra (string): palavra a ser inserida na trie.
            chave (tuple[int, int]): tupla (seção, número) de um documento.
            posicao (int): posição de ocorrência da palavra.
        """

        self.insere_no_recursivo(self.raiz, palavra, chave, posicao)
    
    def insere_no_recursivo(self, no : No, palavra : str, chave : typle, posicao):
        """
        Insere recursivamente uma palavra a partir de um nó.
            
        Parâmetros:
            no (No): nó a ser verificado onde deve inserir a palavra.
            palavra (string): palavra ou restante da palavra a ser inserida na trie.
            chave (tuple[int, int]): tupla (seção, número) de um documento.
            posicao (int): posição de ocorrência da palavra.
        """

        for filho in no.filhos:
            prefixo = prefixo_comum(filho.valor, palavra)

            # Se tem prefixo em comum
            if prefixo:
                # Se o prefixo em comum for exatamente o valor do filho
                if prefixo == filho.valor:
                    resto_palavra = palavra[len(prefixo):]

                    # Se o prefixo é a palavra toda, insere ocorrencia em filho
                    if resto_palavra == "":
                        filho.insere_documento(chave, posicao)
                        return
                    
                    # Continua inserindo o restante da palavra em nó filho
                    self.insere_no_recursivo(filho, resto_palavra, chave, posicao)
                    return

                # Se o prefixo em comum não for todo o valor do filho, fazemos split
                resto_filho = filho.valor[len(prefixo):]
                resto_palavra = palavra[len(prefixo):]

                novo_filho = NoTrie(resto_filho)
                novo_filho.filhos = filho.filhos.copy()
                novo_filho.documentos = filho.documentos.copy()

                filho.valor = prefixo
                filho.filhos = [novo_filho]
                filho.documentos = {}

                if resto_palavra:
                    novo_filho_resto = NoTrie(resto_palavra)
                    novo_filho_resto.insere_documento(chave, posicao)
                    filho.insere_filho(novo_filho_resto)

                else:
                    filho.insere_documento(chave, posicao)

                return

        # Caso não tenha prefixo comum com nenhum filho, cria novo nó
        novo_no = NoTrie(palavra)
        novo_no.insere_documento(chave, posicao)
        no.insere_filho(novo_no)
    
    def busca_palavra(self, palavra : str):
        """
        Busca as ocorrências de uma palavra na Trie, caso tenha.
            
        Parâmetros:
            palavra (string): palavra a ser buscada na trie.

        Retorna:
            A lista de ocorrências da palavra ou a lista vazia, se ela não existe na trie.
        """
        if not isinstance(palavra, str):
            raise TypeError(f"Palavra deve ser string mas recebeu {type(palavra).__name__}")

        return self.busca_no_recursivo(self.raiz, palavra)
    
    def busca_no_recursivo(self, no : NoTrie, palavra : str):
        """
        Busca as ocorrências de uma palavra na Trie, caso tenha, recursivamente.
            
        Parâmetros:
            no (NoTrie): o nó em que é buscada a palavra.
            palavra (string): palavra a ser buscada na trie.

        Retorna:
            A lista de ocorrências da palavra ou a lista vazia, se ela não existe na trie.
        """
        for filho in no.filhos:
            prefixo = prefixo_comum(palavra, filho.valor)

            # Não tem prefixo em comum, então continua
            if prefixo == "":
                continue

            # A palavra e a o valor de filhos são iguais, então palavra foi achada
            if prefixo == palavra and prefixo == filho.valor:
                return filho.documentos
            
            # A palavra ainda não foi totalmente encontrada, então busca recursivamente
            # No filho o restante da palavra
            elif prefixo == filho.valor and len(filho.valor) < len(palavra):
                resto_palavra = palavra[len(prefixo):]
                resultado = self.busca_no_recursivo(filho, resto_palavra)

                if resultado:
                    return resultado
            
            # O prefixo não cobre toda a palavra; palavra não encontrada na Trie
            elif len(prefixo) < len(filho.valor):
                return {}

        return {}