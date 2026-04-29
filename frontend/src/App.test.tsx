import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders FluxHR dashboard heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/fluxhr dashboard/i);
  expect(headingElement).toBeInTheDocument();
});
