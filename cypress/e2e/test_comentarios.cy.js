describe('Comentários em documentos', () => {
  const senha = 'senha_segura_123';
  const autora = `autora_e2e_${Date.now()}`;
  const leitora = `leitora_e2e_${Date.now()}`;
  const urlDocumento = '/documento/tech/010';

  beforeEach(() => {
    cy.deslogar();
  });

  afterEach(() => {
    cy.excluirConta({ usuario: autora, senha });
    cy.excluirConta({ usuario: leitora, senha });
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

  it('deve exibir o comentário para outra usuária sem permitir que ela o exclua', () => {
    const texto = `Comentário visível ${Date.now()}`;

    cy.criarConta({ nome: 'Autora E2E', usuario: autora, senha });
    cy.criarConta({ nome: 'Leitora E2E', usuario: leitora, senha });

    // a autora publica o comentário
    cy.logar({ usuario: autora, senha });
    cy.visit(urlDocumento);
    cy.get('#texto-comentario').type(texto);
    cy.get('#botao-comentar').click();
    cy.contains('.comentario', texto).should('be.visible');

    // outra usuária acessa o mesmo documento
    cy.deslogar();
    cy.logar({ usuario: leitora, senha });
    cy.visit(urlDocumento);

    // ela vê o comentário e a autoria, mas não tem a opção de excluí-lo
    cy.contains('.comentario', texto).within(() => {
      cy.get('.comentario-autor').should('have.text', autora);
      cy.get('.botao-excluir-comentario').should('not.exist');
    });

    // e pode publicar o próprio comentário
    cy.get('#texto-comentario').should('be.visible');
  });
});
