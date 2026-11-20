from src.classes.trie_compacta import TrieCompacta, NoTrie
from src.utils import processar_texto
from src.models import Documento, Categoria
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
                
    def _aplicar_escape(self, valor):
        """Escapa os delimitadores usados no formato do arquivo."""
        if valor is None:
            return ""
    
        valor = str(valor)
        valor = valor.replace('\\', '\\\\')
        valor = valor.replace(':', '\\:')
        valor = valor.replace(',', '\\,')
        valor = valor.replace('(', '\\(')
        valor = valor.replace(')', '\\)')
            
        valor = valor.replace("'", "\\'") 
            
        return valor

    def _remover_escape(self, valor_escapado):
        """Reverte o escalonamento dos delimitadores."""
        valor = valor_escapado.replace('\\:', ':')
        valor = valor.replace('\\,', ',')
        valor = valor.replace('\\(', '(')
        valor = valor.replace('\\)', ')')
        valor = valor.replace("\\'", "'")      
        valor = valor.replace('\\\\', '\\')
            
        return valor

    def parse_linha_trie(self, linha):
        """
        Parse de uma linha do arquivo de índice da trie

        Parâmetros:
            linha (str): a string da linha a ser analisada. Ex: "('ad',{(1, 23):...})"

        Retorno:
            Uma tupla (valor, lista_invertida_dict) com os dados extraídos.
        """
        linha = linha.strip()
        
        # Regex para capturar o valor (str) entre as primeiras aspas simples. Ex: "('valor capturado', ...)"
        match = re.match(r"^\('((?:\\.|[^'])*?)',({.*})\)$", linha)
        
        if not match:
            if linha == "('',{})" or linha == "(,'{}')": 
                return "", {}
            raise ValueError(f"Formato de linha inválido, não correspondeu ao padrão: {linha}")
        
        valor_escapado = match.group(1)   # Ex: "it\'s"
        lista_str = match.group(2)    # Ex: "{(1, 23):{...}}"
            
        valor = self._remover_escape(valor_escapado)
        
        lista_invertida_dict = {}
        
        # Encontra todas as ocorrências de "(cat, num): {'freq': f, 'pos': p}"
        padrao_ocorrencia = re.compile(r"\((\d+),\s*(\d+)\):\s*\{'frequencia':\s*(\d+),\s*'primeira_posicao':\s*(\d+)\}")
        
        # Encontra todas as correspondências na string
        for match_dict in padrao_ocorrencia.finditer(lista_str):
            cat_str, num_str, freq_str, pos_str = match_dict.groups()
            
            # Converte as strings capturadas para inteiros
            chave = (int(cat_str), int(num_str))
            dados = {"frequencia": int(freq_str), "primeira_posicao": int(pos_str)}
            lista_invertida_dict[chave] = dados
            
        return valor, lista_invertida_dict
            
    def _carregar_estatisticas(self, linhas, indice_estatisticas, indice_trie):
        """Processa as linhas de estatísticas e preenche self.estatisticas_corpus."""
        
        for i in range(indice_estatisticas + 1, indice_trie):
                    linha = linhas[i].strip()
                    if not linha: continue
                    
                    # Divide no primeiro ':' que não esteja escapado 
                    partes = re.split(r'(?<!\\):', linha, maxsplit=1)
                    
                    if len(partes) == 2:
                        termo_seguro, estatisticas_str = partes
                        try:
                            termo = self._remover_escape(termo_seguro) 
                            valores_estatisticas = estatisticas_str.split(',')
                            
                            if len(valores_estatisticas) == 2:
                                media_str, desvio_str = valores_estatisticas
                                try:
                                    media = float(media_str)
                                    desvio = float(desvio_str)
                                    self.estatisticas_corpus[termo] = {
                                        "media": media,
                                        "desvio_padrao": desvio
                                    }
                                except ValueError as e_float:
                                    print(f"[ERRO CONVERSÃO] Termo '{termo}': Não foi possível converter '{media_str}' ou '{desvio_str}' para float. Linha: {linha}. Erro: {e_float}")
                            else:
                                print(f"[ERRO FORMATO ESTATISTICAS] Termo '{termo}': Falta vírgula ou formato incorreto. Linha: {linha}")
                        except re.error as e_escape:
                            print(f"[ERRO ESCAPE] Falha ao processar termo escapado na linha {i+1}: '{linha}'. Erro: {e_escape}")
                        except Exception as e_geral:
                            print(f"[ERRO INESPERADO ESTATISTICAS] Linha {i+1}: '{linha}'. Erro: {e_geral}")
                    else:
                        print(f"[ERRO FORMATO LINHA] Linha {i+1}: Não foi possível separar termo e estatísticas (falta ':'?). Conteúdo: '{linha}'")

    def _carregar_trie(self, linhas, indice_trie):
        """Processa as linhas da trie e reconstrói self.trie."""
        self.trie = TrieCompacta()
        pilha_de_pais = [self.trie.raiz] # Pilha para reconstruir a árvore
                
        for i in range(indice_trie + 2, len(linhas)):
            linha = linhas[i]
            if not linha.strip(): continue
            
            # Calcula a profundidade do nó na árvore pela indentação (a cada 2 espaços = 1 nível de profundidade)
            profundidade_atual = (len(linha) - len(linha.lstrip(' '))) // 2
            try:
                valor, lista_invertida_dict = self.parse_linha_trie(linha)

                novo_no = NoTrie(valor)
                novo_no.lista_invertida = lista_invertida_dict

                while len(pilha_de_pais) > profundidade_atual:
                    pilha_de_pais.pop()
                        
                pai_no = pilha_de_pais[-1]
                pai_no.insere_filho(novo_no)
                        
                pilha_de_pais.append(novo_no)
            
            except ValueError as e_parse:
                # Se o parse_linha_trie falhar, este print nos dirá qual linha
                print(f"[ERRO PARSE TRIE] Linha {i+1} mal formatada, pulando nó. Erro: {e_parse}", flush=True)
                print(f"   -> Conteúdo da linha: {linha.strip()}", flush=True)
            except Exception as e_geral:
                print(f"[ERRO FATAL CARREGAR TRIE] Linha {i+1}: {e_geral}")
                print(f"   -> Conteúdo da linha: {linha.strip()}")
                    
    def carregar_de_disco(self, caminho_arquivo):
        """
        Carrega o índice (trie e estatísticas) de um arquivo de texto
        """
        print(f"Carregando dados de '{caminho_arquivo}'...")
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
                
                # Encontra os separadores de bloco
                indice_estatisticas = linhas.index("---ESTATISTICAS---\n")
                indice_trie = linhas.index("---TRIE---\n")
                    
                self._carregar_estatisticas(linhas, indice_estatisticas, indice_trie)
                self._carregar_trie(linhas, indice_trie)
                
            print("Dados carregados com sucesso.")
            return True
        except FileNotFoundError:
            print("Arquivo de 'indice_trie_estatisticas.dat' não encontrado. Um novo será criado.")
            return False
        except Exception as e:
            print(f"Erro ao carregar dados de 'indice_trie_estatisticas.dat': {e}")
            return False
                
    def _formatar_estatisticas(self):
        """Converte o dicionário de estatísticas em uma lista de strings para salvar."""
        linhas_formatadas = []
        
        for termo, estatisticas in self.estatisticas_corpus.items():
            termo_seguro = self._aplicar_escape(termo)
            media = estatisticas['media']
            desvio = estatisticas['desvio_padrao']
            linhas_formatadas.append(f"{termo_seguro}:{media},{desvio}\n")
        return linhas_formatadas
            
    def salvar_em_disco(self, caminho_arquivo):
        """Salva o índice (trie e estatísticas) em um arquivo de texto"""
        print(f"Salvando dados em '{caminho_arquivo}'...")
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write("---ESTATISTICAS---\n")
                
                linhas_estatisticas = self._formatar_estatisticas()
                    
                f.writelines(linhas_estatisticas)

                f.write("---TRIE---\n")
                self._salvar_no_recursivo(f, self.trie.raiz, 0)
            
            print("Dados salvos com sucesso.")
        except IOError as e:
            print(f"Erro ao salvar o índice: {e}")
                
    def _formatar_lista_invertida(self, lista_invertida):
        """Converte o dicionário da lista invertida para uma string"""
        if not lista_invertida:
            return "{}"

        partes = []
        for chave, dados in lista_invertida.items():
            cat, num = chave
            freq = dados["frequencia"]
            pos = dados["primeira_posicao"]
            
            # Constrói a string para um item do dicionário em um formato definido
            parte_str = f"({cat}, {num}):{{'frequencia':{freq}, 'primeira_posicao':{pos}}}"
            partes.append(parte_str)
        
        conteudo_interno = ", ".join(partes)
        return f"{{{conteudo_interno}}}"

    def _salvar_no_recursivo(self, arquivo, no, profundidade):
        """Método auxiliar recursivo para salvar os nós da trie usando indentação para representar a estrutura da árvore."""
        indentacao = "  " * profundidade
        
        lista_invertida_str = self._formatar_lista_invertida(no.lista_invertida)
        
        valor_seguro = self._aplicar_escape(no.valor)
        
        # faz com que o valor do nó seja escrito com aspas (ex: 'ad')
        valor_str = f"'{valor_seguro}'"
        
        arquivo.write(f"{indentacao}({valor_str},{lista_invertida_str})\n")
        
        for filho in no.filhos:
            self._salvar_no_recursivo(arquivo, filho, profundidade + 1)         
    
