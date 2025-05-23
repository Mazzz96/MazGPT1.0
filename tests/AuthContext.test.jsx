import React from 'react';
import { render, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../components/AuthContext';

describe('AuthContext', () => {
  it('provides user and auth functions', () => {
    let context;
    function TestComponent() {
      context = useAuth();
      return null;
    }
    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );
    expect(context).toHaveProperty('user');
    expect(context).toHaveProperty('login');
    expect(context).toHaveProperty('logout');
  });
});
