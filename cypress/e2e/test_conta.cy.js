describe('Fluxo de conta', () => {
    const nome = `teste`;
    const usuario = `teste_${Date.now()}`;
    const senha = '123456';
    const contasCriadas = [{ usuario, senha }];

    const criarConta = (usuarioConta = usuario, senhaConta = senha) => {
        cy.request({
            method: 'POST',
            url: '/criar-usuario',
            form: true,
            body: {
                nome,
                usuario: usuarioConta,
                senha: senhaConta,
                confirmar_senha: senhaConta,
            },
        });
    };

    const logar = (usuarioConta = usuario, senhaConta = senha) => {
        cy.request({
            method: 'POST',
            url: '/login',
            form: true,
            body: {
                usuario: usuarioConta,
                senha: senhaConta,
            },
        });
    };

    const excluirConta = () => {
        cy.request({
            method: 'POST',
            url: '/perfil/deletar',
            form: true,
        });
    };

    beforeEach(() => {
        cy.request({
            method: 'POST',
            url: '/logout',
            failOnStatusCode: false,
        });
        cy.visit('/');
    });

    afterEach(() => {
        contasCriadas.forEach((conta) => {
            cy.request({
                method: 'POST',
                url: '/login',
                form: true,
                body: {
                    usuario: conta.usuario,
                    senha: conta.senha,
                },
                failOnStatusCode: false,
            }).then((resposta) => {
                if (resposta.status !== 401) {
                    excluirConta();
                }
            });
        });
    });

    //TO-DO: setup de deslogar sessão ativa início dos testes
    it('CT01: criar conta', () => {
        cy.visit('/login');
        cy.contains('Criar conta').should('be.visible');

        cy.contains('a', 'Criar conta').click();
        cy.get('#nome').type(nome);
        cy.get('#usuario').type(usuario);
        cy.get('#senha').type(senha);
        cy.get('#confirmar_senha').type(senha);
        cy.get('#botao-busca').click();

        cy.contains('Conta criada. Faça login.').should('be.visible');
    });

    it('CT02: logar na conta', () => {
        criarConta();

        cy.visit('/login');
        cy.contains('Logar').should('be.visible');

        cy.contains('a', 'Logar').click();
        cy.get('#usuario').type(usuario);
        cy.get('#senha').type(senha);
        cy.get('#botao-busca').click();

        cy.contains('Realize consultas sobre o bando de dados').should('be.visible');
    });

    it('CT03: alterar dados da conta', () => {
        criarConta();
        logar();

        const novoUsuario = `alterado_${Date.now()}`;
        const novaSenha = '654321';

        cy.visit('/perfil');
        cy.get('#nome').clear().type('teste alterado');
        cy.get('#usuario').clear().type(novoUsuario);
        cy.get('#senha').type(novaSenha);
        cy.get('#confirmar_senha').type(novaSenha);
        cy.get('#botao-busca').click();

        cy.contains('Perfil atualizado com sucesso.').should('be.visible');
        contasCriadas.push({ usuario: novoUsuario, senha: novaSenha });
    });

    it('CT04: deslogar da conta', () => {
        criarConta();
        logar();

        cy.visit('/');
        cy.get('#logout').click();

        cy.contains('Logar').should('be.visible');
    });
});