from flask import Flask, render_template, request, session, redirect, url_for, abort, flash
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from src.artigos_salvos import RepositorioArtigosSalvosSQLite, ServicoArtigosSalvos
from src.models import Categoria

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-padrao-apenas-para-desenvolvimento")

corpus_index = None
gerenciador_de_busca = None
caminho_corpus = None

DATABASE = os.getenv('DATABASE_PATH', 'usuarios.db')


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


def obter_servico_artigos_salvos() -> ServicoArtigosSalvos:
    servico_configurado = app.config.get('SERVICO_ARTIGOS_SALVOS')
    if servico_configurado is not None:
        return servico_configurado

    repositorio = RepositorioArtigosSalvosSQLite(get_db)
    return ServicoArtigosSalvos(repositorio)

inicializar_banco()


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
        termo = request.form['mensagem']
        return redirect(url_for('search_results', termo = termo))

    return render_template('historico.html', historico = session['historico'])

@app.route('/ajuda')
def ajuda():
    """Exibe a página de ajuda."""
    return render_template('ajuda.html')

if __name__ == '__main__':
    inicializar_indice()
     
    if gerenciador_de_busca:    
        app.run(debug=False) 
    else:
        print("ERRO: Gerenciador de busca não foi inicializado.")
        print("O servidor Flask não será iniciado.")

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

    session.clear()
    flash('Sua conta foi excluída.', 'sucesso')
    return redirect(url_for('login'))


@app.route('/search', methods=['POST'])
def search_results():
    """Recebe uma consulta enviada pelo formulário."""
    mensagem = request.form.get('mensagem', '').strip()
    if not mensagem:
        abort(400, description='A consulta não pode estar vazia.')

    return render_template('index.html')

@app.route('/artigos-salvos', methods=['GET'])
def artigos_salvos():
    """Lista os artigos salvos pelo usuário autenticado."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    servico = obter_servico_artigos_salvos()
    artigos = servico.listar_artigos(session['usuario'])
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
    
    return render_template('exibir_documento.html', documento=documento, artigo_salvo=artigo_salvo,)

if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5000'))
    app.run(host=host, port=port, debug=False)
