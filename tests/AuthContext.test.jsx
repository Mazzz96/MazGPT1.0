import React from 'react';
import { render, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../components/AuthContext';

describe('AuthContext', () => {
  it('provides user and auth functions', () => {
    let context;
    function TestComponent() {
      context = useAuth();
      return null;
    }
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(context).toHaveProperty('user');
    expect(context).toHaveProperty('login');
    expect(context).toHaveProperty('logout');
  });
});
