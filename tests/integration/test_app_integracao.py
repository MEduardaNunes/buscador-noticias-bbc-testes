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


def test_login_redireciona_usuario_autenticado_e_home_renderiza(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta_login = cliente.get("/login", follow_redirects=False)
    resposta_home = cliente.get("/")

    assert resposta_login.status_code == 302
    assert resposta_login.location.endswith("/")
    assert resposta_home.status_code == 200
    assert "Máquina de Busca" in resposta_home.get_data(as_text=True)


def test_criar_usuario_get_renderiza_formulario(cliente):
    resposta = cliente.get("/criar-usuario")

    assert resposta.status_code == 200
    assert b"Criar conta" in resposta.data


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


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "", "usuario": "ana"},
        {"nome": "Ana", "usuario": ""},
    ],
)
def test_perfil_rejeita_nome_ou_usuario_vazio(cliente, dados):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(
        "/perfil",
        data={**dados, "senha": "", "confirmar_senha": ""},
    )

    assert resposta.status_code == 400
    assert "obrigatórios" in resposta.get_data(as_text=True)


def test_perfil_rejeita_nova_senha_curta(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post(
        "/perfil",
        data={
            "nome": "Ana",
            "usuario": "ana",
            "senha": "123",
            "confirmar_senha": "123",
        },
    )

    assert resposta.status_code == 400
    assert "pelo menos 6 caracteres" in resposta.get_data(as_text=True)


def test_perfil_limpa_sessao_quando_usuario_nao_existe(cliente):
    with cliente.session_transaction() as sessao:
        sessao["usuario"] = "removido"

    resposta = cliente.get("/perfil", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")
    with cliente.session_transaction() as sessao:
        assert "usuario" not in sessao


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


def test_deletar_perfil_redireciona_sem_sessao(cliente):
    resposta = cliente.post("/perfil/deletar", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.location.endswith("/login")


def test_busca_rejeita_mensagem_vazia(cliente):
    cadastrar(cliente)
    entrar(cliente)

    resposta = cliente.post("/busca", data={"mensagem": "   "})

    assert resposta.status_code == 400


def test_busca_post_redireciona_para_resultados_e_salva_historico(cliente, monkeypatch):
    monkeypatch.setattr(app, "gerenciador_de_busca", object())

    resposta = cliente.post(
        "/busca",
        data={"mensagem": "  football  "},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/busca?termo=football" in resposta.location
    with cliente.session_transaction() as sessao:
        assert sessao["historico"] == ["football"]


def test_busca_get_executa_consulta_e_mantem_paginacao(cliente, monkeypatch):
    class GerenciadorFalso:
        def executar_busca(self, termo, num_pagina, tamanho_pagina):
            assert termo == "oil"
            assert num_pagina == 2
            assert tamanho_pagina == 10
            return [{
                "id_completo": "business/001",
                "categoria": "business",
                "id_num": "001",
                "score": "1.5",
                "snippet": "<b>oil</b>",
            }]

    monkeypatch.setattr(app, "gerenciador_de_busca", GerenciadorFalso())

    resposta = cliente.get("/busca?termo=oil&page=2")

    assert resposta.status_code == 200
    assert "business/001" in resposta.get_data(as_text=True)
    assert "Página 2" in resposta.get_data(as_text=True)


def test_rota_search_nao_esta_disponivel(cliente):
    resposta = cliente.get("/search")

    assert resposta.status_code == 404


@pytest.mark.parametrize(
    "categoria,doc_id",
    [
        ("invalida", "001"),
        ("business", "abc"),
    ],
)
def test_documento_rejeita_categoria_ou_identificador_invalido(
    cliente, categoria, doc_id
):
    resposta = cliente.get(f"/documento/{categoria}/{doc_id}")

    assert resposta.status_code == 404


def test_documento_renderiza_conteudo_e_estado_de_artigo_salvo(
    cliente, monkeypatch, tmp_path
):
    pasta_categoria = tmp_path / "business"
    pasta_categoria.mkdir()
    (pasta_categoria / "007.txt").write_text("Notícia sobre café", encoding="latin-1")
    monkeypatch.setattr(app, "caminho_corpus", str(tmp_path))

    resposta_anonima = cliente.get("/documento/business/7")
    html_anonimo = resposta_anonima.get_data(as_text=True)

    assert resposta_anonima.status_code == 200
    assert "<h1>Business/007</h1>" in html_anonimo
    assert "Notícia sobre café" in html_anonimo
    assert 'id="botao-salvar-artigo"' in html_anonimo

    cadastrar(cliente)
    entrar(cliente)
    cliente.post(
        "/artigos-salvos/salvar",
        data={"categoria": "business", "doc_id": "007"},
    )

    resposta_salva = cliente.get("/documento/business/7")
    html_salvo = resposta_salva.get_data(as_text=True)

    assert resposta_salva.status_code == 200
    assert 'class="botao-remover-salvo"' in html_salvo


def test_documento_inexistente_retorna_404(cliente, monkeypatch, tmp_path):
    monkeypatch.setattr(app, "caminho_corpus", str(tmp_path))

    resposta = cliente.get("/documento/business/999")

    assert resposta.status_code == 404
    
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


def test_artigos_salvos_exibe_snippet_e_link_para_documento(
    cliente, monkeypatch, tmp_path
):
    pasta_categoria = tmp_path / "business"
    pasta_categoria.mkdir()
    (pasta_categoria / "007.txt").write_text(
        "Título do artigo\n\nPrimeira frase. Segunda frase! Terceira frase.",
        encoding="latin-1",
    )
    monkeypatch.setattr(app, "caminho_corpus", str(tmp_path))
    cadastrar(cliente)
    entrar(cliente)
    cliente.post(
        "/artigos-salvos/salvar",
        data={"categoria": "business", "doc_id": "007"},
    )

    resposta = cliente.get("/artigos-salvos")
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'href="/documento/business/007"' in html
    assert "Primeira frase. Segunda frase!" in html
    assert "Terceira frase." not in html


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
    assert resposta.get_data(as_text=True).count('class="artigo-salvo-item"') == 1

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
    assert "/busca?termo=music" in html
    assert "/busca?termo=economy" in html
    assert html.index("/busca?termo=economy") < html.index("/busca?termo=music")

def test_historico_post_redireciona_para_busca_com_termo(cliente):
    resposta = cliente.post(
        "/historico",
        data={"mensagem": "football"},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.location.endswith("/busca?termo=football")

def test_historico_post_sem_mensagem_retorna_400(cliente):
    resposta = cliente.post("/historico", data={})

    assert resposta.status_code == 400


def test_ajuda_renderiza_pagina_com_instrucoes_de_busca(cliente):
    resposta = cliente.get("/ajuda")

    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Ajuda" in html
    assert "Operadores Lógicos" in html


def test_navegacao_tem_ordem_padronizada_e_seta_condicional(cliente):
    resposta_sem_anterior = cliente.get("/ajuda")
    html_sem_anterior = resposta_sem_anterior.get_data(as_text=True)

    assert resposta_sem_anterior.status_code == 200
    assert 'id="botao-voltar"' not in html_sem_anterior
    ids_botoes = ["botao-inicio", "perfil", "salvos", "historico", "ajuda", "logout"]
    posicoes = [html_sem_anterior.index(f'id="{botao}"') for botao in ids_botoes]
    assert posicoes == sorted(posicoes)

    resposta_com_anterior = cliente.get(
        "/ajuda",
        headers={"Referer": "http://localhost/"},
    )

    assert resposta_com_anterior.status_code == 200
    assert 'id="botao-voltar"' in resposta_com_anterior.get_data(as_text=True)
# -----------
