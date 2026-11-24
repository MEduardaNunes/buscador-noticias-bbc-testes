describe('Gerenciamento de artigos salvos', () => {
  const usuario = `usuario_e2e_${Date.now()}`;
  const senha = 'senha_segura_123';

  beforeEach(() => {
    cy.deslogar();
  });

  afterEach(() => {
    cy.excluirConta({ usuario, senha });
    cy.deslogar();
  });

  it('deve permitir salvar um artigo a partir da página do documento, visualizá-lo na lista de salvos e removê-lo', () => {
    const categoria = 'business';
    const docId = '001';
    const idCompleto = `${categoria}/${docId}`;

    cy.criarConta({ nome: 'Usuário Teste E2E', usuario, senha });
    cy.logar({ usuario, senha });
    cy.visit('/');
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
      .find('.artigo-salvo-remover')
      .click();

    // o artigo não consta mais na lista
    cy.contains('.nome-arquivo', idCompleto).should('not.exist');
  });
});
