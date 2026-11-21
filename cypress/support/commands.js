Cypress.Commands.add('criarConta', ({ nome, usuario, senha }) => {
  return cy.request({
    method: 'POST',
    url: '/criar-usuario',
    form: true,
    body: {
      nome,
      usuario,
      senha,
      confirmar_senha: senha,
    },
  });
});

Cypress.Commands.add(
  'logar',
  ({ usuario, senha, failOnStatusCode = true }) => {
    return cy.request({
      method: 'POST',
      url: '/login',
      form: true,
      body: { usuario, senha },
      failOnStatusCode,
    });
  },
);

Cypress.Commands.add('excluirConta', ({ usuario, senha }) => {
  return cy
    .logar({ usuario, senha, failOnStatusCode: false })
    .then((resposta) => {
      if (resposta.status === 401) {
        return;
      }

      return cy.request({
        method: 'POST',
        url: '/perfil/deletar',
        form: true,
      });
    });
});

Cypress.Commands.add('deslogar', () => {
  return cy.request({
    method: 'POST',
    url: '/logout',
    failOnStatusCode: false,
  });
});