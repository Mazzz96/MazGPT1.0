import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Auth from '../components/Auth.jsx';
import { AuthProvider } from '../components/AuthContext.jsx';

function renderWithProvider(ui) {
  return render(<AuthProvider>{ui}</AuthProvider>);
}

describe('Auth', () => {
  it('renders login form', () => {
    renderWithProvider(<Auth />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('disables inputs and shows spinner while loading', async () => {
    renderWithProvider(<Auth />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'testpass' } });
    const button = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(button);
    expect(button).toBeDisabled();
    expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
  });

  it('shows error if required fields are missing', () => {
    renderWithProvider(<Auth />);
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/all fields are required/i);
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
