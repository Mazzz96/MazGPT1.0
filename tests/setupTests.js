// Jest setup for React Testing Library
import '@testing-library/jest-dom';

// Polyfill for TextEncoder/TextDecoder for Jest
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder;
}

// Add fetch polyfill for Jest test environment
import 'whatwg-fetch';
