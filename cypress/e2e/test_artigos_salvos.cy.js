describe('Gerenciamento de artigos salvos', () => {
  it('deve permitir salvar um artigo a partir da página do documento, visualizá-lo na lista de salvos e removê-lo', () => {
    const sufixo = Date.now();
    const usuario = `usuario_e2e_${sufixo}`;
    const senha = 'senha_segura_123';
    const categoria = 'business';
    const docId = '001';
    const idCompleto = `${categoria}/${docId}`;

    cy.visit('/criar-usuario');
    cy.get('#nome').type('Usuário Teste E2E');
    cy.get('#usuario').type(usuario);
    cy.get('#senha').type(senha);
    cy.get('#confirmar_senha').type(senha);
    cy.get('#botao-busca').click();

    cy.url().should('include', '/login');
    cy.get('#usuario').type(usuario);
    cy.get('#senha').type(senha);
    cy.get('#botao-busca').click();
    cy.url().should('eq', `${Cypress.config('baseUrl')}/`);

    cy.visit(`/documento/${categoria}/${docId}`);
    cy.get('#botao-salvar-artigo').should('be.visible').click();

    // o estado da página do documento reflete que o artigo está salvo
    cy.get('.botao-remover-salvo').should('be.visible');

    // navega para a página de artigos salvos a partir da tela inicial
    cy.visit('/');
    cy.get('#salvos').click();

    // o artigo salvo aparece listado para o usuário
    cy.url().should('include', '/artigos-salvos');
    cy.contains('.nome-arquivo', idCompleto).should('be.visible');

    // remove o artigo diretamente pela lista de salvos
    cy.contains('.resultado-item', idCompleto)
      .find('.botao-remover-salvo')
      .click();

    // o artigo não consta mais na lista
    cy.contains('.nome-arquivo', idCompleto).should('not.exist');
  });
});
