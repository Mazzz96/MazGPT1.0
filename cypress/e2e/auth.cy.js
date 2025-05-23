// Cypress E2E test for MazGPT authentication UI

describe('MazGPT Auth Flow', () => {
  it('should show login form and allow user to sign up and log in', () => {
    cy.visit('/');
    cy.contains('Sign Up').click();
    cy.get('input[name="email"]').type('e2euser@example.com');
    cy.get('input[name="name"]').type('E2E User');
    cy.get('input[name="password"]').type('e2epassword123');
    cy.contains('Create Account').click();
    // Should see login or dashboard after signup
    cy.contains(/login|dashboard/i);
    // Now try logging in
    cy.get('input[name="email"]').clear().type('e2euser@example.com');
    cy.get('input[name="password"]').clear().type('e2epassword123');
    cy.contains('Log In').click();
    cy.contains(/dashboard|welcome|profile/i);
  });
});
