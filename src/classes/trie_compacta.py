from __future__ import annotations

class No:
    """
    Representa um nó da Trie.
    
    Atributos:
        valor (str): string contida no nó
        filhos (list[No]): Nós filhos desse nó.
        documentos (dict[tuple[int, int], dict[str, int]]): dicionário 
            que mapeia uma chave (seção, número) que indica o documento e 
            associa à frequência de ocorrência de uma palavra no documento
            e à primeira ocorrência dessa palavra.
    """

    def __init__(self, valor):
        self.valor = valor
        self.filhos = []
        self.documentos = {}

    def insere_filho(self, filho : No):
        """
        Insere um nó filho em ordem de leitura.
        
        Parâmetros:
            filho (No): nó filho a ser inserido.
        """
        if not isinstance(filho, No):
            raise TypeError(f"Esperado No, mas recebeu {type(filho).__name__}")
            
        self.filhos.append(filho)

    def insere_documento(self, chave : tuple[int, int], posicao_no_doc : int) -> None:
        """
        Atualiza os documentos de um nó com uma nova ocorrência.
        
        Parâmetros:
            chave (tuple[int, int]): tupla (seção, número) de um documento.
            posicao_no_doc (int): posição dentro do documento da palavra.
        """
        if len(chave) != 2:
            raise ValueError("Chave deve conter exatamente dois valores (seção, número do texto)")
            
        if not isinstance(chave[0], int) or not isinstance(chave[1], int):
            raise TypeError(f"Valores das chaves devem ser int, recebido {type(chave[0]).__name__} e {type(chave[1]).__name__}")

        if chave[0] < 0 or chave[1] < 0:
            raise ValueError("Valores das chaves devem ser não negativos.")

        if posicao_no_doc < 0:
            raise ValueError("Valor da posição no documento deve se rnão negativa.")

        if chave in self.documentos:
            self.documentos[chave]["frequencia"] += 1

        else:
            self.documentos[chave] = {
                "frequencia": 1,
                "primeira_posicao": posicao_no_doc
            }