"""Módulo de Recuperação de Informação (RI)

    A gramática utilizada para processar uma consulta é a seguinte:
        <exp>         ::= <exp_or>                  
        <exp_or>      ::= <exp_and> (OR <exp_and>)* 
        <exp_and>     ::= <exp_not> (AND <exp_not>)*      
        <exp_not>     ::= NOT <exp_not> | <subexp>   
        <subexp>      ::= "(" <exp> ")" | <palavra> 
        <palavra> ::= (<letra> | <digito> | <simbolo>)*  
        <letra> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m"
                  | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"
                  | "á" | "à" | "â" | "ã" | "ä" | "ç" | "é" | "è" | "ê" | "í" | "ì" | "ó" | "ò" 
                  | "ô" | "õ" | "ö" | "ú" | "ù" | "ü" | "ñ"
        <digito> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" 
        <simbolo> ::= "." | "&" | "%" | "$" | "," | "!" | "?" | "#" | "@" | ";" 
                    | "[" | "]" | "{" | "}" | "_" | "+" | "=" | "*" | "/" | ":" 
                    | "~" | "^" | "<" | ">" | "|" | "'" | "-" | "£" | "\\" 
"""
from __future__ import annotations

import sys
import os
import re
import traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classes.trie_compacta import TrieCompacta
from src.utilitarios import normaliza_query
from src.modelos import Categoria


class NoParsing:
    """
    Representa um nó da árvore de Parsing
    
    Atributos:
        operador (str): operador do Nó (AND, OR, NOT ou palavra).
        direita (NoParsing): filho à direita do nó.
        esquerda (NoParsing): filho à esquerda do nó.
    """
    def __init__(self, operador : str, direita : NoParsing | None = None, esquerda : NoParsing | None= None):
        caracteres = r"[a-záàãâäçéèêíìóòôõöúùüñ0-9'\-\.&%£\$,!?#@;\[\]\{\}_\+=\*/:~\^<>|\\]+"

        if not isinstance(operador, str):
            raise TypeError(f"Operador deve ser str, mas recebeu {type(operador).__name__}")

        if operador not in ("AND", "OR", "NOT") and re.fullmatch(caracteres, operador) is None:
            raise ValueError(f"Operador não é AND, OR, NOT ou uma palavra do dicionário, recebido {operador}")

        if direita is not None and not isinstance(direita, NoParsing):
            raise TypeError(f"Nó da direita deve ser NoParsing, mas recebeu {type(direita).__name__}")

        if esquerda is not None and not isinstance(esquerda, NoParsing):
            raise TypeError(f"Nó da esquerda deve ser NoParsing, mas recebeu {type(esquerda).__name__}")

        self.operador = operador
        self.direita = direita
        self.esquerda = esquerda

    def __repr__(self):
        if self.operador in ("AND", "OR"):
            return f"({self.esquerda} {self.operador} {self.direita})"
        
        elif self.operador == "NOT":
            return f"({self.operador} {self.direita})"
        
        else:
            return self.operador


class ArvoreParsing:
    """
    Representa uma árvore de Parsing.
    
    Atributos:
        query (str): string que representa a consulta a ser realizada.
        tokens (lista de str): lista dos tokens gerados a partir da query.
        raiz (NoParsing): armazena a raiz da árvore de parsing.
    """
    def __init__(self, query : str = ""):
        if not isinstance(query, str):
            raise TypeError(f"Query esperada do tipo str, mas recebeu {type(query).__name__}")

        self.query = query
        self.tokens = self.gera_tokens()
        self.raiz = None
        self.pos = 0

    def gera_tokens(self):
        """
        Gera lista de tokens a partir da query da árvore.
        
        Retorna:
            A lista de tokens gerada a partir da query.
        """ 
        query_normalizada = normaliza_query(self.query)
        return query_normalizada.split()

    def token_atual(self):
        """
        Retorna o token atual que está sendo processado.
        
        Retorna:
            O token atual ou None, caso todos tenham sido processados.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        
        return None

    def consome_token(self, esperado : str = ""):
        """
        Consome o token atual, verificando se o token é igual ao esperado (se fornecido).
        Caso o token não corresponda ao esperado, lança ValueError.

        Parâmetros:
            esperado (str): token esperado a ser consumido.
        
        Retorna:
            O token consumido.
        """
        token = self.token_atual()

        if esperado in ("AND", "OR", "NOT", "(", ")"):
            valor_esperado = esperado

        else:
            valor_esperado = "palavra"

        if token is None:
            raise ValueError(f"Fim inesperado de tokens, esperado \" {valor_esperado} \"")

        if esperado and token != esperado:
            raise ValueError(f"Token esperado \" {valor_esperado} \" diferente do token atual \" {token} \"")

        self.pos += 1
        return token
    
    def parse_exp(self):
        """
        Representação da regra de <exp>, sendo ela
            <exp> ::= <exp_or>
        
        Retorna:
            O nó gerado pela regra <exp_or>.
        """
        return self.parse_or()
    
    def parse_or(self):
        """
        Representação da regra de <exp_or>. Processa recursivamente uma 
        expressão or, sendo ela
            <exp_or> ::= <exp_and> (OR <exp_and>)* 
     
        Retorna:
            O nó gerado pelo processamento recursivo.
        """
        no_atual = self.parse_and()
        if no_atual is None:
            return None
        
        while self.token_atual() == "OR":
            self.consome_token("OR")

            no_direita = self.parse_and()
            if no_direita is None:
                raise ValueError("Não existe expressão esperada após OR")
            
            if no_atual is None:
                raise ValueError("Não existe expressão esperada antes de OR")
            
            no_atual = NoParsing("OR", direita=no_direita, esquerda=no_atual)

        return no_atual
    
    def parse_and(self):
        """
        Representação da regra de <exp_and>. Processa recursivamente uma 
        expressão and, sendo ela
            <exp_and> ::= <exp_not> (AND <exp_not>)*      
        
        Retorna:
            O nó gerado pelo processamento recursivo.
        """
        no_atual = self.parse_not()
        if no_atual is None:
            return None

        while self.token_atual() == "AND":
            self.consome_token("AND")

            no_direita = self.parse_not()
            if no_direita is None:
                raise ValueError("Não existe expressão esperada após AND")
            
            if no_atual is None:
                raise ValueError("Não existe expressão esperada antes de AND")

            no_atual = NoParsing("AND", direita=no_direita, esquerda=no_atual)

        return no_atual
    
    def parse_not(self):
        """
        Representação da regra de <exp_not>. Processa recursivamente uma 
        expressão not, sendo ela
            <exp_not> ::= NOT <exp_not> | <subexp>   
        
        Retorna:
            O nó gerado pelo processamento recursivo.
        """
        if self.token_atual() == "NOT":
            self.consome_token("NOT")

            if self.token_atual() is None:
                raise ValueError("Não existe expressão esperada após NOT")
            
            no_direita = self.parse_not()
            if no_direita is None:
                raise ValueError("Não existe expressão esperada após NOT")
            
            return NoParsing("NOT", no_direita)

        else:
            return self.parse_subexp()
    
    def parse_subexp(self):
        """
        Representação da regra de <sub_exp>. Processa recursivamente uma 
        sub-expressão. 
            <subexp> ::= "(" <exp> ")" | <palavra> 
            <palavra> ::= (<letra> | <digito> | <simbolo>)*  
            <letra> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m"
                      | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"
                      | "á" | "à" | "â" | "ã" | "ä" | "ç" | "é" | "è" | "ê" | "í" | "ì" | "ó" | "ò" 
                      | "ô" | "õ" | "ö" | "ú" | "ù" | "ü" | "ñ"
            <digito> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" 
            <simbolo> ::= "." | "&" | "%" | "$" | "," | "!" | "?" | "#" | "@" | ";" 
                        | "[" | "]" | "{" | "}" | "_" | "+" | "=" | "*" | "/" | ":" 
                        | "~" | "^" | "<" | ">" | "|" | "'" | "-" | "£" | "\\" 
        
        Retorna:
            O nó gerado pelo processamento recursivo.
        """

        padrao = r"[a-záàãâäçéèêíìóòôõöúùüñ0-9'\-\.&%£\$,!?#@;\[\]\{\}_\+=\*/:~\^<>|\\]+$"

        if self.token_atual() == "(":
            self.consome_token("(")

            if self.token_atual() == ")":
                raise ValueError("Parênteses vazio")

            no_atual = self.parse_exp()

            if no_atual is None:
                raise ValueError("Expressão do parênteses não existe")
            
            if self.token_atual() != ")":
                raise ValueError("Falta de parênteses fechando a expressão")

            self.consome_token(")")

            return no_atual
        
        elif re.match(padrao, self.token_atual() or "") and self.token_atual() not in ("AND", "OR", "NOT", "(", ")"):
            palavra = self.consome_token()
            return NoParsing(palavra)
        
        else:
            raise ValueError(f"Token inesperado \" {self.token_atual()} \"")
    
    def gera_parsing_tokens(self):
        """
        Gera a árvore de parsing a partir dos tokens da gramática.
        
        Retorna:
            O nó raiz da árvore de parsing.
        """
        if not self.tokens:
            raise ValueError("Consulta vazia")

        self.pos = 0
        self.raiz = None
        self.raiz = self.parse_exp()

        if self.raiz is None:
            raise ValueError("ERRO: parsing falhou, expressão incompleta ou inválida")

        if self.pos < len(self.tokens):
            self.raiz = None
            raise ValueError("ERRO: tokens não consumidos")

        return self.raiz


class GerenciadorDeBusca:
    """Coordena a consulta de forma completa (parsing, busca booleana, cálculo de relevância e formatação)."""

    def __init__(self, trie_index: TrieCompacta, todos_documentos: set, caminho_corpus: str, estatisticas_corpus: dict):
        self.trie = trie_index # Referência ao índice invertido
        self.todos_documentos = todos_documentos # Todos os ids de documentos
        self.caminho_corpus = caminho_corpus # Caminho dos dados
        self.estatisticas_corpus = estatisticas_corpus # Dicionário com estatísticas para o cálculo do z-score
        self.mapa_categorias = {c.value: c.name for c in Categoria} # Usado para formatar o doc_id na saída

    def _tem_no_invalido(self, no):
        """
        Verifica recursivamente se um nó é inválido, ou seja, se algum
        de seus filhos obrigatórios é None.

        Parâmetros:
            no (NoParsing): o nó a ser verificado.

        Retorna:
            True se for inválido, False caso contrário.
        """
        if no is None:
            return True

        if no.operador in ("AND", "OR"):
            return self._tem_no_invalido(no.esquerda) or self._tem_no_invalido(no.direita)

        if no.operador == "NOT":
            return self._tem_no_invalido(no.direita)

        return False

    def _arvore_eh_valida(self, arvore):
        """
        Verifica se uma árvore é válida, isto é, sem raiz nula e sem
        nós inválidos.

        Parâmetros:
            arvore (NoParsing): a árvore a ser verificada.

        Retorna:
            True se for válida, ou False caso contrário.
        """
        if arvore is None:
            return False

        return not self._tem_no_invalido(arvore)

    def _processa_arvore_parsing(self, no: NoParsing):
        """
        Processa uma árvore de parsing recursivamente, aplicando operações booleanas sobre os
        termos dos documentos armazenados na Trie Compacta.

        Parâmetros:
            no (NoParsing): o nó que será processado.

        Retorna:
            Um set com todos os documentos que satisfazem a consulta.
        """
        if no is None:
            return set()

        if no.operador == "AND":
            return (self._processa_arvore_parsing(no.esquerda)
                    & self._processa_arvore_parsing(no.direita))

        elif no.operador == "OR":
            return (self._processa_arvore_parsing(no.esquerda)
                    | self._processa_arvore_parsing(no.direita))

        elif no.operador == "NOT":
            return self.todos_documentos - self._processa_arvore_parsing(no.direita)

        else:
            palavra = no.operador
            documentos_da_palavra = self.trie.busca_palavra(palavra)
            return set(documentos_da_palavra.keys()) if documentos_da_palavra else set()

    def _coletar_termos_query(self, no: NoParsing, termos: set = None):
        """
        Percorre a árvore de parsing recursivamente, coletando todos os nós que
        representam palavras (termos) e ignorando os operadores (AND, OR, NOT).

        Parâmetros:
            no (NoParsing): o nó atual a ser processado (começando pela raiz).
            termos (set): o conjunto acumulador de termos únicos.

        Retorna:
            Um set de strings contendo todos os termos únicos da consulta.
        """
        if termos is None:
            termos = set()

        if no is None:
            return termos

        # Verifica se o nó é uma palavra
        if no.operador not in ("AND", "OR", "NOT"):
            termos.add(no.operador)
            return termos

        # Processa o filho da esquerda (para AND e OR)
        self._coletar_termos_query(no.esquerda, termos)

        # Processa o filho da direita (para AND, OR e NOT)
        self._coletar_termos_query(no.direita, termos)

        return termos

    def _realiza_consulta(self, query):
        """
        Realiza uma consulta sobre o conjunto de documentos, por meio da trie compacta
        que armazena todas as palavras e de uma árvore de parsing que processa a query.

        Parâmetros:
            query (str): a consulta a ser realizada.

        Retorna:
            Uma tupla (documentos, arvore), em que documentos é o conjunto de tuplas
            (seção, número) que satisfazem a consulta e arvore é a raiz da árvore de parsing.
            Caso a consulta seja inválida, retorna (set(), None).
        """
        try:
            parser = ArvoreParsing(query)
            arvore = parser.gera_parsing_tokens()

            if self._arvore_eh_valida(arvore):
                documentos = self._processa_arvore_parsing(arvore)
                return documentos, arvore

            print("ERRO: Árvore de parsing inválida.")
            return set(), None

        except ValueError as e:
            print("ERRO de parsing: ", e)
            return set(), None

    def _calcular_scores_por_documento(self, doc_ids: set, lista_tokens_validos: list):
        """
        Monta um dicionário com z-score, posição e frequência de cada termo para cada documento relevante.

        Parâmetros:
            doc_ids (set): documentos que passaram na busca booleana.
            lista_tokens_validos (list): termos da consulta.

        Retorna:
            Dicionário {doc_id: {'termo_scores': [{'z_score', 'posicao', 'termo', 'freq'}, ...]}}.
        """
        dados_por_doc_id = {}

        for termo in lista_tokens_validos:
            documentos_do_termo = self.trie.busca_palavra(termo)
            stats = self.estatisticas_corpus.get(termo, {"media": 0, "desvio_padrao": 0})

            media = stats['media']
            desvio = stats['desvio_padrao']

            # Se o termo não existe na Trie, pula para o próximo termo
            if not documentos_do_termo:
                continue

            # Itera apenas nos documentos que passaram na busca booleana
            for doc_id in doc_ids:
                # Verifica se o doc atual (da busca booleana) contém o termo atual
                if doc_id in documentos_do_termo:

                    dados = documentos_do_termo[doc_id]
                    freq = dados['frequencia']
                    pos = dados['primeira_posicao']

                    # Cálculo do z-score: (frequência - média) / desvio padrão
                    z_score = (freq - media) / desvio if desvio != 0 else 0

                    if doc_id not in dados_por_doc_id:
                        dados_por_doc_id[doc_id] = {'termo_scores': []}

                    dados_por_doc_id[doc_id]['termo_scores'].append({
                        'z_score': z_score,
                        'posicao': pos,
                        'termo': termo,
                        'freq': freq
                    })
        return dados_por_doc_id
