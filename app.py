from flask import Flask, render_template, request, session, redirect, url_for, abort
import os
import traceback
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-padrao-apenas-para-desenvolvimento")

corpus_index = None
gerenciador_de_busca = None
caminho_corpus = None
                    
@app.route('/', methods=['GET'])
def home():
    """Página inicial com o formulário de busca."""
    return render_template('index.html')


@app.route('/historico', methods=['GET'])
def historico():
    """Página de histórico de consultas."""
    return "Histórico de consultas", 200


@app.route('/ajuda', methods=['GET'])
def ajuda():
    """Página de ajuda sobre operadores e consultas."""
    return "Ajuda sobre consultas e operadores", 200


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