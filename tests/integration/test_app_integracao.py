import pytest

import app

from src.artigos_salvos import ServicoArtigosSalvos

@pytest.fixture
def cliente(tmp_path, monkeypatch):
    banco = tmp_path / "usuarios-teste.db"
    monkeypatch.setattr(app, "DATABASE", str(banco))
    app.inicializar_banco()

    app.app.config.update(TESTING=True, SECRET_KEY="chave-teste")
    with app.app.test_client() as client:
        yield client


def cadastrar(client, nome="Ana Silva", usuario="ana", senha="123456"):
    return client.post(
        "/criar-usuario",
        data={
            "nome": nome,
            "usuario": usuario,
            "senha": senha,
            "confirmar_senha": senha,
        },
        follow_redirects=False,
    )


def entrar(client, usuario="ana", senha="123456"):
    return client.post(
        "/login",
        data={"usuario": usuario, "senha": senha},
        follow_redirects=False,
    )


def test_home_redireciona_usuario_nao_autenticado(cliente):
    resposta = cliente.get("/", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")


def test_login_renderiza_tela_sem_sessao(cliente):
    resposta = cliente.get("/login")

    assert resposta.status_code == 200
    assert b"Logar" in resposta.data


def test_criar_usuario_e_fazer_login(cliente):
    cadastro = cadastrar(cliente)
    login = entrar(cliente)

    assert cadastro.status_code == 302
    assert cadastro.location.endswith("/login")
    assert login.status_code == 302
    assert login.location.endswith("/")

    with cliente.session_transaction() as sessao:
        assert sessao["usuario"] == "ana"
        assert sessao["nome"] == "Ana Silva"


def test_login_rejeita_senha_incorreta(cliente):
    cadastrar(cliente)

    resposta = entrar(cliente, senha="senhaerrada")

    assert resposta.status_code == 401
    assert b"Usu\xc3\xa1rio ou senha inv\xc3\xa1lidos" in resposta.data


def test_usuario_duplicado_nao_pode_ser_cadastrado(cliente):
    cadastrar(cliente)

    resposta = cadastrar(cliente, nome="Outra Ana", usuario="ana")

    assert resposta.status_code == 409
    assert b"j\xc3\xa1 est\xc3\xa1 cadastrado" in resposta.data


def test_cadastro_valida_campos_obrigatorios(cliente):
    resposta = cliente.post(
        "/criar-usuario",
        data={"nome": "", "usuario": "", "senha": "", "confirmar_senha": ""},
    )

    assert resposta.status_code == 400


def test_cadastro_valida_confirmacao_e_tamanho_da_senha(cliente):
    senha_diferente = cliente.post(
        "/criar-usuario",
        data={"nome": "Ana", "usuario": "ana", "senha": "123456", "confirmar_senha": "654321"},
    )
    senha_curta = cliente.post(
        "/criar-usuario",
        data={"nome": "Ana", "usuario": "ana", "senha": "123", "confirmar_senha": "123"},
    )

    assert senha_diferente.status_code == 400
    assert b"n\xc3\xa3o coincidem" in senha_diferente.data
    assert senha_curta.status_code == 400
    assert b"6 caracteres" in senha_curta.data


def test_pagina_perfil_exibe_usuario_autenticado(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.get("/perfil")

    assert resposta.status_code == 200
    assert b"Ana Silva" in resposta.data
    assert b"ana" in resposta.data


def test_perfil_redireciona_sem_sessao(cliente):
    resposta = cliente.get("/perfil", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")


def test_perfil_aceita_duplicidade_de_usuario(cliente):
    cadastrar(cliente)
    cadastrar(cliente, nome="Bia", usuario="bia")
    entrar(cliente)

    resposta = cliente.post(
        "/perfil",
        data={"nome": "Ana Nova", "usuario": "bia", "senha": "", "confirmar_senha": ""},
    )

    assert resposta.status_code == 409
    assert b"j\xc3\xa1 est\xc3\xa1 cadastrado" in resposta.data


def test_perfil_atualiza_nome_usuario_e_senha(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(
        "/perfil",
        data={
            "nome": "Ana Nova",
            "usuario": "ana-nova",
            "senha": "654321",
            "confirmar_senha": "654321",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 200

    with cliente.session_transaction() as sessao:
        assert sessao["usuario"] == "ana-nova"
        assert sessao["nome"] == "Ana Nova"

    cliente.post("/logout")
    login_novo = entrar(cliente, usuario="ana-nova", senha="654321")

    assert login_novo.status_code == 302


def test_perfil_valida_confirmacao_da_nova_senha(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(
        "/perfil",
        data={"nome": "Ana", "usuario": "ana", "senha": "654321", "confirmar_senha": "123456"},
    )

    assert resposta.status_code == 400
    assert b"n\xc3\xa3o coincidem" in resposta.data


def test_logout_limpa_sessao_e_redireciona(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post("/logout", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")

    with cliente.session_transaction() as sessao:
        assert "usuario" not in sessao


def test_deletar_perfil_exclui_usuario_e_limpa_sessao(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post("/perfil/deletar", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")

    with cliente.session_transaction() as sessao:
        assert "usuario" not in sessao

    novo_login = entrar(cliente)
    assert novo_login.status_code == 401


def test_busca_rejeita_mensagem_vazia(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post("/search", data={"mensagem": "   "})

    assert resposta.status_code == 400
    
# App.py: Beatriz
def test_obter_servico_artigos_salvos_retorna_padrao_quando_nao_configurado(cliente):
    servico = app.obter_servico_artigos_salvos()

    assert isinstance(servico, ServicoArtigosSalvos)


def test_obter_servico_artigos_salvos_retorna_instancia_configurada(cliente, monkeypatch):
    servico_customizado = object()
    monkeypatch.setitem(app.app.config, "SERVICO_ARTIGOS_SALVOS", servico_customizado)

    servico = app.obter_servico_artigos_salvos()

    assert servico is servico_customizado

@pytest.mark.parametrize(
    "metodo,rota,dados",
    [
        ("get", "/artigos-salvos", None),
        ("post", "/artigos-salvos/salvar", {"categoria": "tech", "doc_id": "001"}),
        ("post", "/artigos-salvos/remover", {"categoria": "tech", "doc_id": "001"}),
    ],
)
def test_rotas_artigos_salvos_redirecionam_sem_sessao(cliente, metodo, rota, dados):
    resposta = getattr(cliente, metodo)(rota, data=dados, follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")


def test_artigos_salvos_exibe_estado_vazio_para_usuario_sem_artigos(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.get("/artigos-salvos")

    assert resposta.status_code == 200
    assert "Você ainda não salvou nenhum artigo." in resposta.get_data(as_text=True)

def test_salvar_artigo_persiste_e_lista_para_usuario_autenticado(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(
        "/artigos-salvos/salvar",
        data={"categoria": "tech", "doc_id": "001"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "tech/001" in resposta.get_data(as_text=True)


def test_salvar_artigo_duplicado_nao_duplica_na_lista(cliente):
    cadastrar(cliente)
    entrar(cliente)
    cliente.post("/artigos-salvos/salvar", data={"categoria": "sport", "doc_id": "010"})

    resposta = cliente.post(
        "/artigos-salvos/salvar",
        data={"categoria": "sport", "doc_id": "010"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert resposta.get_data(as_text=True).count("sport/010") == 1

def test_remover_artigo_exclui_registro_da_lista(cliente):
    cadastrar(cliente)
    entrar(cliente)
    cliente.post("/artigos-salvos/salvar", data={"categoria": "politics", "doc_id": "005"})

    resposta = cliente.post(
        "/artigos-salvos/remover",
        data={"categoria": "politics", "doc_id": "005"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "politics/005" not in resposta.get_data(as_text=True)


def test_artigos_salvos_isola_registros_entre_usuarios(cliente):
    cadastrar(cliente, nome="Ana", usuario="ana")
    cadastrar(cliente, nome="Bruno", usuario="bruno")

    entrar(cliente, usuario="ana")
    cliente.post("/artigos-salvos/salvar", data={"categoria": "tech", "doc_id": "001"})
    cliente.post("/logout")

    entrar(cliente, usuario="bruno")
    resposta = cliente.get("/artigos-salvos")

    assert resposta.status_code == 200
    assert "tech/001" not in resposta.get_data(as_text=True)

def test_salvar_artigo_respeita_parametro_next(cliente):
    cadastrar(cliente)
    entrar(cliente)
    destino = "/documento/business/001"

    resposta = cliente.post(
        "/artigos-salvos/salvar",
        data={"categoria": "business", "doc_id": "001", "next": destino},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.location.endswith(destino)


def test_remover_artigo_respeita_parametro_next(cliente):
    cadastrar(cliente)
    entrar(cliente)
    destino = "/documento/business/001"
    cliente.post("/artigos-salvos/salvar", data={"categoria": "business", "doc_id": "001"})

    resposta = cliente.post(
        "/artigos-salvos/remover",
        data={"categoria": "business", "doc_id": "001", "next": destino},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.location.endswith(destino)

@pytest.mark.parametrize(
    "rota,categoria,doc_id",
    [
        ("/artigos-salvos/salvar", "invalida", "001"),
        ("/artigos-salvos/salvar", "tech", "abc"),
        ("/artigos-salvos/remover", "invalida", "001"),
        ("/artigos-salvos/remover", "tech", ""),
    ],
)
def test_salvar_ou_remover_artigo_com_dados_invalidos_retorna_400(cliente, rota, categoria, doc_id):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(rota, data={"categoria": categoria, "doc_id": doc_id})

    assert resposta.status_code == 400

def test_historico_get_inicializa_lista_vazia_na_sessao(cliente):
    resposta = cliente.get("/historico")

    assert resposta.status_code == 200
    with cliente.session_transaction() as sessao:
        assert sessao["historico"] == []


def test_historico_get_exibe_termos_salvos_em_ordem_reversa(cliente):
    with cliente.session_transaction() as sessao:
        sessao["historico"] = ["music", "economy"]

    resposta = cliente.get("/historico")

    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "/search?termo=music" in html
    assert "/search?termo=economy" in html
    assert html.index("/search?termo=economy") < html.index("/search?termo=music")

def test_historico_post_redireciona_para_busca_com_termo(cliente):
    resposta = cliente.post(
        "/historico",
        data={"mensagem": "football"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.location.endswith("/search?termo=football")

def test_historico_post_sem_mensagem_retorna_400(cliente):
    resposta = cliente.post("/historico", data={})

    assert resposta.status_code == 400


def test_ajuda_renderiza_pagina_com_instrucoes_de_busca(cliente):
    resposta = cliente.get("/ajuda")

    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Ajuda" in html
    assert "Operadores Lógicos" in html
# -----------
