import { act as reactAct } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';

// Export act from react instead of react-dom/test-utils
export const act = reactAct;

// Re-export commonly used testing utilities
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

// Custom render function with providers
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, options);
}