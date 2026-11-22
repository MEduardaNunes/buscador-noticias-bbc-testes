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


def test_texto_do_comentario_e_escapado_no_html(cliente):
    cadastrar_e_entrar(cliente)

    resposta = cliente.post(URL_COMENTAR, data={"texto": "<script>alert(1)</script>"}, follow_redirects=True)
    html = resposta.get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_visitante_ve_comentarios_mas_nao_ve_formulario_nem_botao_de_excluir(cliente):
    cadastrar_e_entrar(cliente)
    cliente.post(URL_COMENTAR, data={"texto": "Comentário da Ana"})
    cliente.post("/logout")

    html = cliente.get(URL_DOCUMENTO).get_data(as_text=True)

    assert "Comentário da Ana" in html
    assert 'id="texto-comentario"' not in html
    assert "botao-excluir-comentario" not in html


def test_autor_exclui_o_proprio_comentario_pela_pagina(cliente):
    cadastrar_e_entrar(cliente)
    cliente.post(URL_COMENTAR, data={"texto": "Vou apagar"})
    comentario_id = comentarios_do_documento()[0]["id"]

    resposta = cliente.post(f"/comentarios/{comentario_id}/excluir", follow_redirects=True)

    assert resposta.status_code == 200
    assert "Comentário excluído." in resposta.get_data(as_text=True)
    assert comentarios_do_documento() == []


def test_excluir_comentario_de_outro_usuario_retorna_403(cliente):
    cadastrar_e_entrar(cliente, usuario="ana")
    cliente.post(URL_COMENTAR, data={"texto": "Comentário da Ana"})
    comentario_id = comentarios_do_documento()[0]["id"]
    cliente.post("/logout")
    cadastrar_e_entrar(cliente, usuario="bia")

    resposta = cliente.post(f"/comentarios/{comentario_id}/excluir")

    assert resposta.status_code == 403
    assert len(comentarios_do_documento()) == 1
