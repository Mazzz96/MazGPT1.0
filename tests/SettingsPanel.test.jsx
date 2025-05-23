import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SettingsPanel from '../components/SettingsPanel.jsx';

describe('SettingsPanel', () => {
  const mockSetPreferences = jest.fn();
  const basePrefs = { theme: 'light', language: 'en', fontSize: 16, notifications: false, mapProvider: 'google' };

  it('renders preferences form', () => {
    render(<SettingsPanel preferences={basePrefs} setPreferences={mockSetPreferences} />);
    expect(screen.getByLabelText(/theme/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enable notifications/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/map provider/i)).toBeInTheDocument();
  });

  it('changes theme and language', () => {
    render(<SettingsPanel preferences={basePrefs} setPreferences={mockSetPreferences} />);
    fireEvent.change(screen.getByLabelText(/theme/i), { target: { value: 'dark' } });
    expect(mockSetPreferences).toHaveBeenCalledWith(expect.objectContaining({ theme: 'dark' }));
    fireEvent.change(screen.getByLabelText(/language/i), { target: { value: 'es' } });
    expect(mockSetPreferences).toHaveBeenCalledWith(expect.objectContaining({ language: 'es' }));
  });

  it('toggles notifications', () => {
    render(<SettingsPanel preferences={basePrefs} setPreferences={mockSetPreferences} />);
    fireEvent.click(screen.getByLabelText(/enable notifications/i));
    expect(mockSetPreferences).toHaveBeenCalledWith(expect.objectContaining({ notifications: true }));
  });

  // Add more tests for map provider, export/delete/change password buttons, and accessibility as needed
});
