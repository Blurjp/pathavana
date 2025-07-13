/**
 * Testing utilities for Pathavana frontend.
 * 
 * Provides common utilities, custom render functions, and helpers
 * for testing React components with proper context providers.
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { SidebarProvider } from '../../contexts/SidebarContext';
import userEvent from '@testing-library/user-event';

// Mock user for testing
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  first_name: 'Test',
  last_name: 'User',
  email_verified: true,
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Custom render options
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Auth context options
  authenticated?: boolean;
  user?: typeof mockUser | null;
  
  // Router options
  initialEntries?: string[];
  
  // Sidebar context options
  sidebarOpen?: boolean;
  
  // Additional wrapper components
  wrapper?: React.ComponentType<{ children: React.ReactNode }>;
}

// All providers wrapper
const AllTheProviders: React.FC<{
  children: React.ReactNode;
  authenticated?: boolean;
  user?: typeof mockUser | null;
  initialEntries?: string[];
  sidebarOpen?: boolean;
}> = ({ 
  children, 
  authenticated = true, 
  user = mockUser,
  initialEntries = ['/'],
  sidebarOpen = false 
}) => {
  // Mock auth context value
  const authContextValue = {
    user: authenticated ? user : null,
    login: jest.fn(),
    logout: jest.fn(),
    loading: false,
    error: null,
    isAuthenticated: authenticated,
    token: authenticated ? 'mock-token' : null,
    refreshToken: jest.fn(),
  };

  // Mock sidebar context value
  const sidebarContextValue = {
    isOpen: sidebarOpen,
    toggle: jest.fn(),
    open: jest.fn(),
    close: jest.fn(),
  };

  return (
    <BrowserRouter>
      <AuthProvider>
        <SidebarProvider>
          {children}
        </SidebarProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult => {
  const {
    authenticated = true,
    user = mockUser,
    initialEntries = ['/'],
    sidebarOpen = false,
    wrapper: Wrapper,
    ...renderOptions
  } = options;

  let WrapperComponent = ({ children }: { children: React.ReactNode }) => (
    <AllTheProviders
      authenticated={authenticated}
      user={user}
      initialEntries={initialEntries}
      sidebarOpen={sidebarOpen}
    >
      {children}
    </AllTheProviders>
  );

  if (Wrapper) {
    WrapperComponent = ({ children }: { children: React.ReactNode }) => (
      <AllTheProviders
        authenticated={authenticated}
        user={user}
        initialEntries={initialEntries}
        sidebarOpen={sidebarOpen}
      >
        <Wrapper>{children}</Wrapper>
      </AllTheProviders>
    );
  }

  return render(ui, { wrapper: WrapperComponent, ...renderOptions });
};

// Render with router only
export const renderWithRouter = (
  ui: ReactElement,
  { initialEntries = ['/'], ...options }: { initialEntries?: string[] } & RenderOptions = {}
): RenderResult => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>{children}</BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...options });
};

// Render with auth context only
export const renderWithAuth = (
  ui: ReactElement,
  options: {
    authenticated?: boolean;
    user?: typeof mockUser | null;
  } & RenderOptions = {}
): RenderResult => {
  const { authenticated = true, user = mockUser, ...renderOptions } = options;

  const authContextValue = {
    user: authenticated ? user : null,
    login: jest.fn(),
    logout: jest.fn(),
    loading: false,
    error: null,
    isAuthenticated: authenticated,
    token: authenticated ? 'mock-token' : null,
    refreshToken: jest.fn(),
  };

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>
      {children}
    </AuthProvider>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Create user event instance
export const createUserEvent = () => userEvent;

// Mock functions factory
export const createMockFunctions = () => ({
  mockNavigate: jest.fn(),
  mockApiCall: jest.fn(),
  mockOnClick: jest.fn(),
  mockOnChange: jest.fn(),
  mockOnSubmit: jest.fn(),
  mockOnSuccess: jest.fn(),
  mockOnError: jest.fn(),
});

// Wait for element helpers
export const waitForElement = async (
  getElement: () => HTMLElement | null,
  timeout = 5000
): Promise<HTMLElement> => {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const element = getElement();
    if (element) {
      return element;
    }
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  
  throw new Error(`Element not found within ${timeout}ms`);
};

// Form testing helpers
export const fillForm = async (
  user: typeof userEvent,
  formData: Record<string, string>
) => {
  for (const [fieldName, value] of Object.entries(formData)) {
    const field = document.querySelector(`[name="${fieldName}"]`) as HTMLInputElement;
    if (field) {
      await user.clear(field);
      await user.type(field, value);
    }
  }
};

export const submitForm = async (
  user: typeof userEvent,
  form?: HTMLFormElement
) => {
  const formElement = form || document.querySelector('form');
  if (formElement) {
    const submitButton = formElement.querySelector('button[type="submit"]') ||
                        formElement.querySelector('input[type="submit"]');
    if (submitButton) {
      await user.click(submitButton as HTMLElement);
    }
  }
};

// Mock API responses
export const mockApiResponses = {
  login: {
    success: {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockUser,
    },
    failure: {
      detail: 'Invalid credentials',
    },
  },
  
  travelSessions: {
    success: {
      sessions: [
        {
          session_id: 'session-1',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
          plan_data: {
            destination: 'Paris, France',
          },
        },
      ],
      total: 1,
    },
  },
  
  flightSearch: {
    success: {
      flights: [
        {
          id: 'flight-1',
          origin: 'JFK',
          destination: 'CDG',
          price: { total: 850, currency: 'USD' },
          airline: 'Air France',
          duration: '8h 30m',
        },
      ],
      search_metadata: {
        search_id: 'search-123',
        total_results: 1,
      },
    },
  },
  
  hotelSearch: {
    success: {
      hotels: [
        {
          id: 'hotel-1',
          name: 'Grand Hotel Paris',
          price: { total: 200, currency: 'USD' },
          rating: 4.5,
          location: { address: 'Paris Center' },
        },
      ],
      search_metadata: {
        search_id: 'search-456',
        total_results: 1,
      },
    },
  },
};

// Error simulation helpers
export const simulateNetworkError = () => {
  return Promise.reject(new Error('Network Error'));
};

export const simulateApiError = (status: number, message: string) => {
  const error = new Error(message) as any;
  error.response = {
    status,
    data: { detail: message },
  };
  return Promise.reject(error);
};

// Performance testing helpers
export const measureRenderTime = (renderFn: () => void): number => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

// Screenshot/snapshot helpers
export const createSnapshot = (component: RenderResult) => {
  return component.container.innerHTML;
};

// Accessibility testing helpers
export const checkAccessibility = async (container: HTMLElement) => {
  // This would integrate with @axe-core/react in a real implementation
  const violations = [];
  
  // Check for basic accessibility issues
  const missingAltImages = container.querySelectorAll('img:not([alt])');
  if (missingAltImages.length > 0) {
    violations.push('Images missing alt text');
  }
  
  const missingLabels = container.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
  if (missingLabels.length > 0) {
    violations.push('Form inputs missing labels');
  }
  
  return violations;
};

// Local storage helpers
export const mockLocalStorage = () => {
  const storage: Record<string, string> = {};
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    }),
    key: jest.fn((index: number) => Object.keys(storage)[index] || null),
    get length() {
      return Object.keys(storage).length;
    },
  };
};

// Session storage helpers
export const mockSessionStorage = () => {
  const storage: Record<string, string> = {};
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    }),
    key: jest.fn((index: number) => Object.keys(storage)[index] || null),
    get length() {
      return Object.keys(storage).length;
    },
  };
};

// Console spy helpers
export const spyOnConsole = () => {
  const originalConsole = { ...console };
  const consoleMethods = ['log', 'warn', 'error', 'info', 'debug'] as const;
  const spies: Record<string, jest.SpyInstance> = {};
  
  consoleMethods.forEach(method => {
    spies[method] = jest.spyOn(console, method).mockImplementation(() => {});
  });
  
  return {
    spies,
    restore: () => {
      consoleMethods.forEach(method => {
        spies[method].mockRestore();
      });
    },
  };
};

// Export everything
export * from '@testing-library/react';
export { customRender as render };
export { userEvent };

// Re-export common testing utilities
export {
  screen,
  fireEvent,
  waitFor,
  act,
  cleanup,
} from '@testing-library/react';