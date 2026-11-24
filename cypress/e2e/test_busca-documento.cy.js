describe('Busca e visualização de documento', () => {
  const usuario = `usuario_busca_${Date.now()}`;
  const senha = 'senha_segura_123';

  beforeEach(() => {
    cy.deslogar();
  });

  afterEach(() => {
    cy.excluirConta({ usuario, senha });
    cy.deslogar();
  });

  it('deve buscar um termo, abrir o primeiro documento retornado e registrar no histórico', () => {
    const termoBusca = 'music';

    cy.criarConta({ nome: 'Usuário Teste E2E', usuario, senha });
    cy.logar({ usuario, senha });
    cy.visit('/');

    // realiza a busca pela interface
    cy.get('input[name="mensagem"]').type(termoBusca);
    cy.get('#botao-busca').click();

    // redirecionou para /busca e exibiu pelo menos um resultado clicável
    cy.url().should('include', `/busca?termo=${termoBusca}`);
    cy.get('a.resultado-link').should('have.length.greaterThan', 0);

    // abre o primeiro documento da lista
    cy.get('a.resultado-link').first().click();

    // navega para /documento/<categoria>/<id> e exibe conteúdo não vazio
    cy.url().should('match', /\/documento\/[^/]+\/\d+$/);
    cy.get('.conteudo-documento')
      .should('be.visible')
      .invoke('text')
      .should('match', /\S+/);

    // acessa o histórico
    cy.visit('/historico');

    // confirma que o termo buscado foi registrado na sessão
    cy.contains('a.item_historico', termoBusca).should('be.visible');
  });
});

