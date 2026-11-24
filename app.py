from flask import Flask, render_template, request, session, redirect, url_for, abort, flash
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from src.artigos_salvos import RepositorioArtigosSalvosSQLite, ServicoArtigosSalvos
from src.comentarios import (
    ComentarioNaoEncontradoError,
    PermissaoNegadaError,
    RepositorioComentariosSQLite,
    ServicoComentarios,
)
from src.modelos import Categoria
from src.classes.indexer import Corpus
from src.busca import GerenciadorDeBusca
from src.snippet import gerar_snippet_primeiras_frases
import traceback

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-padrao-apenas-para-desenvolvimento")

corpus_index = None
gerenciador_de_busca = None
caminho_corpus = None

DATABASE = os.getenv('DATABASE_PATH', 'usuarios.db')


def inicializar_indice():
    """
    Carrega o índice do disco ou o constrói se não existir.
    Inicializa as variáveis globais que a aplicação usará.
    """
    global corpus_index, caminho_corpus, mapa_categorias_reverso, gerenciador_de_busca
    caminho_indice_salvo = "data-bbc/indice_trie_estatisticas.dat" 
    caminho_relativo = './data-bbc'
    
    # Define o caminho absoluto para o corpus
    caminho_corpus = os.path.abspath(os.path.join(os.path.dirname(__file__), caminho_relativo))

    corpus_index = Corpus()
    indice_carregado_ou_construido = False
    
    # Tenta carregar o índice do disco
    if os.path.exists(caminho_indice_salvo) and corpus_index.carregar_de_disco(caminho_indice_salvo):
        print("O índice foi carregado do arquivo")
        indice_carregado_ou_construido = True
    else:
        # Se falhar constrói o índice
        if not os.path.exists(caminho_corpus):
            print(f"ERRO: Diretório do corpus não encontrado em '{caminho_corpus}'")
            return

        corpus_index.construir_indice(caminho_corpus)
        
        if corpus_index.estatisticas_corpus:
            print("\nO índice foi criado e carregado na memória") 
            os.makedirs(os.path.dirname(caminho_indice_salvo), exist_ok=True)
            corpus_index.salvar_em_disco(caminho_indice_salvo)
            indice_carregado_ou_construido = True
        else:
            print("\nERRO: O índice não pôde ser criado. Verifique os logs") 

    # Se o índice estiver pronto inicializa o Gerenciador de Busca
    if indice_carregado_ou_construido:
        try:
            todos_documentos = corpus_index.todos_documentos 
            
            gerenciador_de_busca = GerenciadorDeBusca(
                trie_index=corpus_index.trie,
                todos_documentos=todos_documentos,
                caminho_corpus=caminho_corpus,
                estatisticas_corpus=corpus_index.estatisticas_corpus
            )      
        except Exception as e:
            print(f"[ERRO] Falha ao criar GerenciadorDeBusca: {e}")
            traceback.print_exc()


def get_db():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco():
    with get_db() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            )
            """
        )
    RepositorioArtigosSalvosSQLite(get_db).inicializar_tabela()
    RepositorioComentariosSQLite(get_db).inicializar_tabela()


def obter_servico_artigos_salvos() -> ServicoArtigosSalvos:
    servico_configurado = app.config.get('SERVICO_ARTIGOS_SALVOS')
    if servico_configurado is not None:
        return servico_configurado

    repositorio = RepositorioArtigosSalvosSQLite(get_db)
    return ServicoArtigosSalvos(repositorio)


def obter_servico_comentarios() -> ServicoComentarios:
    servico_configurado = app.config.get('SERVICO_COMENTARIOS')
    if servico_configurado is not None:
        return servico_configurado

    repositorio = RepositorioComentariosSQLite(get_db)
    return ServicoComentarios(repositorio)

inicializar_banco()

@app.before_request
def inicializar_sessao():
    """Executa antes de cada rota para garantir que o histórico exista."""
    session.permanent = False
    if 'historico' not in session:
        session['historico'] = []

@app.route('/', methods=['GET'])
def home():
    """Página inicial com o formulário de busca."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Autentica um usuário existente."""
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')

        with get_db() as conexao:
            registro = conexao.execute(
                'SELECT * FROM usuarios WHERE usuario = ?',
                (usuario,),
            ).fetchone()

        if registro is None or not check_password_hash(registro['senha_hash'], senha):
            flash('Usuário ou senha inválidos.', 'erro')
            return render_template('login.html', modo='login'), 401

        session.clear()
        session['usuario'] = registro['usuario']
        session['nome'] = registro['nome']
        return redirect(url_for('home'))

    if 'usuario' in session:
        return redirect(url_for('home'))

    return render_template('login.html', modo='login')


@app.route('/criar-usuario', methods=['GET', 'POST'])
def criar_usuario():
    """Cria uma nova conta local."""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')
        confirmacao = request.form.get('confirmar_senha', '')

        if not nome or not usuario or not senha:
            flash('Preencha nome, usuário e senha.', 'erro')
            return render_template('login.html', modo='criar'), 400

        if senha != confirmacao:
            flash('As senhas não coincidem.', 'erro')
            return render_template('login.html', modo='criar'), 400

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'erro')
            return render_template('login.html', modo='criar'), 400

        try:
            with get_db() as conexao:
                conexao.execute(
                    'INSERT INTO usuarios (nome, usuario, senha_hash) VALUES (?, ?, ?)',
                    (nome, usuario, generate_password_hash(senha)),
                )
        except sqlite3.IntegrityError:
            flash('Este usuário já está cadastrado.', 'erro')
            return render_template('login.html', modo='criar'), 409

        flash('Conta criada. Faça login.', 'sucesso')
        return redirect(url_for('login'))

    return render_template('login.html', modo='criar')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/historico', methods=['GET', 'POST'])
def historico():
    """Exibe o histórico de buscas e permite nova busca a partir dele."""
    
    if 'historico' not in session:
        session['historico'] = []

    if request.method == 'POST':
        termo = request.form.get('mensagem', '').strip()
        if not termo:
            abort(400, description='A consulta não pode estar vazia.')
        return redirect(url_for('busca_resultados', termo=termo))

    return render_template('historico.html', historico = session['historico'])

@app.route('/ajuda')
def ajuda():
    """Exibe a página de ajuda."""
    return render_template('ajuda.html')


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    """Exibe e atualiza os dados do usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_atual = session['usuario']

    with get_db() as conexao:
        registro = conexao.execute(
            'SELECT id, nome, usuario, senha_hash FROM usuarios WHERE usuario = ?',
            (usuario_atual,),
        ).fetchone()

    if registro is None:
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        novo_usuario = request.form.get('usuario', '').strip()
        nova_senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not novo_usuario:
            flash('Nome e usuário são obrigatórios.', 'erro')
            return render_template('perfil.html', perfil=registro), 400

        if novo_usuario != usuario_atual:
            with get_db() as conexao:
                usuario_existente = conexao.execute(
                    'SELECT id FROM usuarios WHERE usuario = ?',
                    (novo_usuario,),
                ).fetchone()

            if usuario_existente is not None:
                flash('Este nome de usuário já está cadastrado.', 'erro')
                return render_template('perfil.html', perfil=registro), 409

        senha_hash = registro['senha_hash']
        if nova_senha:
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem.', 'erro')
                return render_template('perfil.html', perfil=registro), 400

            if len(nova_senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'erro')
                return render_template('perfil.html', perfil=registro), 400

            senha_hash = generate_password_hash(nova_senha)

        with get_db() as conexao:
            conexao.execute(
                'UPDATE usuarios SET nome = ?, usuario = ?, senha_hash = ? WHERE id = ?',
                (nome, novo_usuario, senha_hash, registro['id']),
            )

        session['usuario'] = novo_usuario
        session['nome'] = nome
        flash('Perfil atualizado com sucesso.', 'sucesso')

        with get_db() as conexao:
            registro = conexao.execute(
                'SELECT id, nome, usuario, senha_hash FROM usuarios WHERE id = ?',
                (registro['id'],),
            ).fetchone()

        return render_template('perfil.html', perfil=registro)

    return render_template('perfil.html', perfil=registro)


@app.route('/perfil/deletar', methods=['POST'])
def deletar_perfil():
    """Exclui definitivamente o usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_atual = session['usuario']

    with get_db() as conexao:
        conexao.execute('DELETE FROM usuarios WHERE usuario = ?', (usuario_atual,))

    obter_servico_comentarios().excluir_comentarios_do_usuario(usuario_atual)

    session.clear()
    flash('Sua conta foi excluída.', 'sucesso')
    return redirect(url_for('login'))


def _processar_busca():
    """Processa consultas enviadas por formulário ou pelos parâmetros da URL."""
    resultados_pagina = []
    termo = None
    pagina_atual = 1
    tamanho_pagina_fixo = 10
    tem_proxima_pagina = False

    if request.method == 'POST':
        termo = request.form.get('mensagem', '').strip()
        if not termo:
            abort(400, description='A consulta não pode estar vazia.')

        if termo not in session['historico']:
            session['historico'].append(termo)
            session['historico'] = session['historico'][-10:]
            session.modified = True
        return redirect(url_for(request.endpoint, termo=termo))

    termo = request.args.get('termo', '').strip()
    try:
        pagina_atual = int(request.args.get('page', 1))
        if pagina_atual < 1:
            pagina_atual = 1
    except (TypeError, ValueError):
        pagina_atual = 1

    if termo and gerenciador_de_busca:
        try:
            retorno_busca = gerenciador_de_busca.executar_busca(
                termo,
                num_pagina=pagina_atual,
                tamanho_pagina=tamanho_pagina_fixo,
            )
            resultados_pagina = retorno_busca if isinstance(retorno_busca, list) else []

            if not resultados_pagina and pagina_atual > 1:
                return redirect(url_for(request.endpoint, termo=termo, page=1))

            tem_proxima_pagina = len(resultados_pagina) == tamanho_pagina_fixo
        except Exception as erro:
            print(f"Erro durante o processamento da busca para '{termo}': {erro}")
            traceback.print_exc()
            resultados_pagina = []
            tem_proxima_pagina = False

    return render_template(
        'resultados_busca.html',
        termo=termo,
        resultados=resultados_pagina,
        pagina_atual=pagina_atual,
        tem_proxima_pagina=tem_proxima_pagina,
    )


@app.route('/busca', methods=['GET', 'POST'])
def busca_resultados():
    return _processar_busca()


@app.route('/artigos-salvos', methods=['GET'])
def artigos_salvos():
    """Lista os artigos salvos pelo usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    servico = obter_servico_artigos_salvos()
    artigos = servico.listar_artigos(session['usuario'])

    raiz_corpus = caminho_corpus or os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data-bbc')
    )
    categorias_validas = {categoria.name for categoria in Categoria}
    for artigo in artigos:
        categoria = artigo['categoria']
        doc_id = artigo['doc_id']
        if categoria not in categorias_validas or not doc_id.isdigit():
            artigo['snippet'] = '[Documento inválido]'
            continue

        nome_arquivo = f"{int(doc_id):03d}.txt"
        caminho_arquivo = os.path.join(raiz_corpus, categoria, nome_arquivo)
        try:
            with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                conteudo = arquivo.read()
        except FileNotFoundError:
            print(f"[Aviso Artigos Salvos] Documento não encontrado: {caminho_arquivo}")
            artigo['snippet'] = '[Documento não encontrado]'
        else:
            artigo['snippet'] = gerar_snippet_primeiras_frases(conteudo)

    return render_template('artigos_salvos.html', artigos=artigos)


@app.route('/artigos-salvos/salvar', methods=['POST'])
def salvar_artigo():
    """Salva um artigo para o usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    categoria = request.form.get('categoria', '').strip()
    doc_id = request.form.get('doc_id', '').strip()
    proximo = request.form.get('next') or url_for('artigos_salvos')

    servico = obter_servico_artigos_salvos()
    try:
        inserido = servico.salvar_artigo(session['usuario'], categoria, doc_id)
        if inserido:
            flash('Artigo salvo com sucesso.', 'sucesso')
        else:
            flash('Este artigo já estava salvo.', 'sucesso')
    except ValueError as erro:
        abort(400, description=str(erro))

    return redirect(proximo)


@app.route('/artigos-salvos/remover', methods=['POST'])
def remover_artigo():
    """Remove um artigo da lista de salvos do usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    categoria = request.form.get('categoria', '').strip()
    doc_id = request.form.get('doc_id', '').strip()
    proximo = request.form.get('next') or url_for('artigos_salvos')

    servico = obter_servico_artigos_salvos()
    try:
        servico.remover_artigo(session['usuario'], categoria, doc_id)
        flash('Artigo removido dos salvos.', 'sucesso')
    except ValueError as erro:
        abort(400, description=str(erro))

    return redirect(proximo)
    
@app.route('/documento/<categoria>/<id_documento>', methods=['GET'])
def exibir_documento(categoria, id_documento):
    """Exibe o conteúdo de um documento específico."""
    global caminho_corpus

    # Verifica se a categoria é válida
    categorias_validas = [c.name for c in Categoria]
    if categoria not in categorias_validas:
        print(f"ERRO: Categoria inválida '{categoria}'")
        abort(404, "Documento não encontrado.")

    # Verifica se o id é completamente numérico
    if not id_documento.isdigit():
        print(f"ERRO: id de documento inválido '{id_documento}'")
        abort(404, "Documento não encontrado.")
    
    id_formatado = f"{int(id_documento):03d}" 
    nome_arquivo = f"{id_formatado}.txt"
    
    caminho_arquivo = os.path.join(caminho_corpus, categoria, nome_arquivo)
    
    caminho_absoluto_corpus = os.path.abspath(caminho_corpus)
    caminho_absoluto_arquivo = os.path.abspath(caminho_arquivo)
    
    if not os.path.exists(caminho_absoluto_arquivo):
        print(f"ERRO: Arquivo não encontrado em {caminho_absoluto_arquivo}") 
        abort(404, "Documento não encontrado.")
    
    with open(caminho_arquivo, 'r', encoding='latin-1') as f:
        conteudo = f.read()
            
    documento = {
        'categoria': categoria, 
        'id': id_formatado, 
        'conteudo': conteudo
    }

    artigo_salvo = False
    if 'usuario' in session:
        artigo_salvo = obter_servico_artigos_salvos().artigo_esta_salvo(session['usuario'], categoria, id_formatado)
    
    comentarios = obter_servico_comentarios().listar_comentarios(categoria, id_formatado)

    return render_template(
        'exibir_documento.html',
        documento=documento,
        artigo_salvo=artigo_salvo,
        comentarios=comentarios,
    )


@app.route('/documento/<categoria>/<id_documento>/comentarios', methods=['POST'])
def comentar_documento(categoria, id_documento):
    """Publica um comentário do usuário autenticado no documento."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    texto = request.form.get('texto', '')
    try:
        obter_servico_comentarios().comentar(session['usuario'], categoria, id_documento, texto)
        flash('Comentário publicado.', 'sucesso')
    except ValueError as erro:
        flash(str(erro), 'erro')

    return redirect(url_for('exibir_documento', categoria=categoria, id_documento=id_documento, _anchor='comentarios'))


@app.route('/comentarios/<int:comentario_id>/excluir', methods=['POST'])
def excluir_comentario(comentario_id):
    """Exclui um comentário, desde que o usuário autenticado seja o autor."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        comentario = obter_servico_comentarios().excluir_comentario(session['usuario'], comentario_id)
    except ComentarioNaoEncontradoError:
        abort(404, description='Comentário não encontrado.')
    except PermissaoNegadaError:
        abort(403, description='Você só pode excluir os seus próprios comentários.')

    flash('Comentário excluído.', 'sucesso')
    return redirect(url_for('exibir_documento', categoria=comentario['categoria'], id_documento=comentario['doc_id'], _anchor='comentarios'))

if __name__ == '__main__':
    inicializar_indice()

    if gerenciador_de_busca:
        host = os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('PORT', '5000'))
        app.run(host=host, port=port, debug=False)
    else:
        print("ERRO: Gerenciador de busca não foi inicializado.")
        print("O servidor Flask não será iniciado.")
