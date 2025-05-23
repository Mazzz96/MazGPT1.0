// Cypress E2E smoke test for MazGPT main UI

describe('MazGPT Smoke Test', () => {
  it('loads the homepage and shows main UI elements', () => {
    cy.visit('/');
    cy.contains(/MazGPT|Chat|Sign Up|Log In/i);
    cy.get('nav').should('exist');
    cy.get('main').should('exist');
  });
});
