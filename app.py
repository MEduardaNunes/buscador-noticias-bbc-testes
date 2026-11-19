from flask import Flask, render_template, request, session, redirect, url_for, abort, flash
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

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


@app.route('/historico', methods=['GET'])
def historico():
    """Página de histórico de consultas."""
    return "Histórico de consultas", 200


@app.route('/ajuda', methods=['GET'])
def ajuda():
    """Página de ajuda sobre operadores e consultas."""
    return "Ajuda sobre consultas e operadores", 200

@app.route('/perfil', methods=['GET'])
def perfil():
    """Página de perfil do usuário"""
    return "Perfil", 200


@app.route('/search', methods=['POST'])
def search_results():
    """Recebe uma consulta enviada pelo formulário."""
    mensagem = request.form.get('mensagem', '').strip()
    if not mensagem:
        abort(400, description='A consulta não pode estar vazia.')

    return render_template('index.html')


if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5000'))
    app.run(host=host, port=port, debug=False)