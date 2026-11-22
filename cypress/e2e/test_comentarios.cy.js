describe('Comentários em documentos', () => {
  const senha = 'senha_segura_123';
  const autora = `autora_e2e_${Date.now()}`;
  const urlDocumento = '/documento/tech/010';

  beforeEach(() => {
    cy.deslogar();
  });

  afterEach(() => {
    cy.excluirConta({ usuario: autora, senha });
    cy.deslogar();
  });

  it('deve permitir publicar um comentário em um documento e excluí-lo', () => {
    const texto = `Comentário de teste ${Date.now()}`;

    cy.criarConta({ nome: 'Autora E2E', usuario: autora, senha });
    cy.logar({ usuario: autora, senha });
    cy.visit(urlDocumento);

    // publica o comentário pelo formulário da página do documento
    cy.get('#texto-comentario').type(texto);
    cy.get('#botao-comentar').click();

    // o comentário aparece na lista, identificado com a autora
    cy.contains('.auth-mensagem', 'Comentário publicado.').should('be.visible');
    cy.contains('.comentario', texto)
      .should('be.visible')
      .find('.comentario-autor')
      .should('have.text', autora);

    // a autora exclui o próprio comentário
    cy.contains('.comentario', texto).find('.botao-excluir-comentario').click();

    // o comentário não consta mais na página
    cy.contains('.auth-mensagem', 'Comentário excluído.').should('be.visible');
    cy.contains('.comentario', texto).should('not.exist');
  });
});
