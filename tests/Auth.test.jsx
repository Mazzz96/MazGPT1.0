import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Auth from '../components/Auth.jsx';
import { AuthProvider } from '../components/AuthContext.jsx';
import { MemoryRouter } from 'react-router-dom';

function renderWithProvider(ui) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
}

describe('Auth', () => {
  it('renders login form', () => {
    renderWithProvider(<Auth />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    // Use getAllByLabelText to avoid duplicate label error
    const passwordInputs = screen.getAllByLabelText(/password/i);
    expect(passwordInputs.length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('disables inputs and shows spinner while loading', async () => {
    renderWithProvider(<Auth />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    const passwordInputs = screen.getAllByLabelText(/password/i);
    fireEvent.change(passwordInputs[0], { target: { value: 'testpass' } });
    const button = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(button);
    expect(button).toBeDisabled();
    // Use getAllByLabelText for loading spinner
    expect(screen.getAllByLabelText(/loading/i).length).toBeGreaterThan(0);
  });

  it('shows error if required fields are missing', async () => {
    renderWithProvider(<Auth />);
    // Wait for loading spinner to disappear (loading false)
    await waitFor(() => {
      expect(screen.queryByLabelText(/loading/i)).toBeNull();
    });
    const button = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(button);
    const alert = await screen.findByRole('alert');
    await waitFor(() => {
      expect(alert).toHaveTextContent(/all fields are required/i);
    });
  });

  it('switches to signup and back', () => {
    renderWithProvider(<Auth />);
    fireEvent.click(screen.getByText(/sign up/i));
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/sign in/i));
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  // Mock 2FA prompt and error feedback as needed
  // ...additional tests for 2FA, reset, and error/success feedback...
});
