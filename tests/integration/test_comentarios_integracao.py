import pytest

import app

URL_DOCUMENTO = "/documento/business/7"
URL_COMENTAR = "/documento/business/7/comentarios"


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "DATABASE", str(tmp_path / "comentarios-teste.db"))
    app.inicializar_banco()

    pasta_categoria = tmp_path / "corpus" / "business"
    pasta_categoria.mkdir(parents=True)
    (pasta_categoria / "007.txt").write_text("Notícia sobre café", encoding="latin-1")
    monkeypatch.setattr(app, "caminho_corpus", str(tmp_path / "corpus"))

    app.app.config.update(TESTING=True, SECRET_KEY="chave-teste")
    with app.app.test_client() as client:
        yield client


def cadastrar_e_entrar(client, usuario="ana", senha="123456"):
    client.post(
        "/criar-usuario",
        data={"nome": usuario.title(), "usuario": usuario, "senha": senha, "confirmar_senha": senha},
    )
    client.post("/login", data={"usuario": usuario, "senha": senha})


def comentarios_do_documento():
    return app.obter_servico_comentarios().listar_comentarios("business", "007")


def test_publicar_comentario_sem_login_redireciona_e_nao_salva(cliente):
    resposta = cliente.post(URL_COMENTAR, data={"texto": "Comentário anônimo"})

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")
    assert comentarios_do_documento() == []


def test_comentario_publicado_aparece_na_pagina_do_documento(cliente):
    cadastrar_e_entrar(cliente)

    resposta = cliente.post(URL_COMENTAR, data={"texto": "Adorei a notícia"}, follow_redirects=True)
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Comentário publicado." in html
    assert "Adorei a notícia" in html
    assert "Comentários (1)" in html


def test_comentario_vazio_exibe_mensagem_de_erro_e_nao_salva(cliente):
    cadastrar_e_entrar(cliente)

    resposta = cliente.post(URL_COMENTAR, data={"texto": "     "}, follow_redirects=True)

    assert "O comentário não pode estar vazio." in resposta.get_data(as_text=True)
    assert comentarios_do_documento() == []
