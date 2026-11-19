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
