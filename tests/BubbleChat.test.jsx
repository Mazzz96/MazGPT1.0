import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AuthProvider } from '../components/AuthContext.jsx';
import BubbleChat from '../components/BubbleChat.jsx';

// Mock props and context
const mockSetMessages = jest.fn();
const mockSetProjects = jest.fn();
const mockSetPreferences = jest.fn();
const mockSetProjectId = jest.fn();

const defaultProps = {
  projectId: 'default',
  setProjectId: mockSetProjectId,
  projects: [{ id: 'default', name: 'Default' }],
  setProjects: mockSetProjects,
  messages: [],
  setMessages: mockSetMessages,
  preferences: { theme: 'light', fontSize: 16 },
  setPreferences: mockSetPreferences,
};

function renderWithProvider(ui, props = {}) {
  return render(
    <AuthProvider>
      {React.cloneElement(ui, props)}
    </AuthProvider>
  );
}

describe('BubbleChat', () => {
  it('renders chat input and send button', () => {
    renderWithProvider(<BubbleChat {...defaultProps} />);
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('disables send button and input when loading or aiTyping', () => {
    renderWithProvider(<BubbleChat {...defaultProps} />, { loading: true });
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
    expect(screen.getByLabelText(/message input/i)).toBeDisabled();
  });

  it('shows error message if error state is set', () => {
    renderWithProvider(<BubbleChat {...defaultProps} error="Test error" />);
    expect(screen.getByRole('alert')).toHaveTextContent(/test error/i);
  });

  it('shows MazGPT is typing indicator when aiTyping', () => {
    renderWithProvider(<BubbleChat {...defaultProps} />, { aiTyping: true });
    expect(screen.getByText(/MazGPT is typing/i)).toBeInTheDocument();
  });

  // Add more tests for message sending, tooltips, and mobile responsiveness as needed
});
