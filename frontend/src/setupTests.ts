/**
 * Jest setup configuration for Pathavana frontend testing.
 * 
 * This file configures the testing environment, sets up global mocks,
 * and provides common utilities for all tests.
 */

import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import React from 'react';
// import { server } from './tests/utils/mockServer';

// Configure React Testing Library
configure({
  testIdAttribute: 'data-testid',
  asyncWrapper: async (cb) => {
    let result;
    await act(async () => {
      result = await cb();
    });
    return result;
  },
});

// Global test setup
beforeAll(() => {
  // Start MSW server for API mocking
  // server.listen({
  //   onUnhandledRequest: 'warn',
  // });
  
  // Mock console methods to reduce noise in tests
  global.console = {
    ...console,
    // Uncomment to hide console logs during tests
    // log: jest.fn(),
    // debug: jest.fn(),
    // info: jest.fn(),
    // warn: jest.fn(),
    // error: jest.fn(),
  };
});

// Reset handlers after each test
afterEach(() => {
  // server.resetHandlers();
  
  // Clear all mocks
  jest.clearAllMocks();
  
  // Clear localStorage
  localStorage.clear();
  
  // Clear sessionStorage
  sessionStorage.clear();
});

// Clean up after all tests
afterAll(() => {
  // server.close();
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
});

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
};

Object.defineProperty(navigator, 'geolocation', {
  value: mockGeolocation,
});

// Mock fetch if not already mocked by MSW
if (!global.fetch) {
  global.fetch = jest.fn();
}

// Mock environment variables
process.env.REACT_APP_API_BASE_URL = 'http://localhost:8000';
process.env.REACT_APP_ENVIRONMENT = 'test';

// Add custom Jest matchers
expect.extend({
  toBeInTheDocument: (received) => {
    const pass = received && received.ownerDocument && received.ownerDocument.contains(received);
    return {
      pass,
      message: () => `expected element ${pass ? 'not ' : ''}to be in the document`,
    };
  },
});

// Global test utilities
global.act = require('@testing-library/react').act;

// Mock timers helper
global.mockTimers = () => {
  jest.useFakeTimers();
  return {
    advanceTimers: (ms: number) => jest.advanceTimersByTime(ms),
    runOnlyPendingTimers: () => jest.runOnlyPendingTimers(),
    runAllTimers: () => jest.runAllTimers(),
    restore: () => jest.useRealTimers(),
  };
};

// Error boundary for test isolation
class TestErrorBoundary extends React.Component {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Test Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if ((this.state as any).hasError) {
      return React.createElement('div', { 'data-testid': 'error-boundary' }, 'Something went wrong.');
    }

    return (this.props as any).children;
  }
}

global.TestErrorBoundary = TestErrorBoundary;

// Common test data
global.mockUser = {
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

global.mockTravelSession = {
  session_id: 'test-session-123',
  user_id: 1,
  status: 'active',
  session_data: {
    messages: [
      {
        role: 'user',
        content: 'I want to plan a trip to Paris',
        timestamp: '2024-01-01T00:00:00Z',
      },
    ],
    parsed_intent: {
      destination: 'Paris',
      travel_type: 'leisure',
    },
  },
  plan_data: {
    destination: 'Paris, France',
    departure_date: '2024-06-01',
    return_date: '2024-06-08',
    travelers: 2,
  },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_activity_at: '2024-01-01T00:00:00Z',
};

global.mockFlightData = {
  id: 'flight-123',
  origin: 'JFK',
  destination: 'CDG',
  departure_date: '2024-06-01',
  return_date: '2024-06-08',
  airline: 'Air France',
  flight_number: 'AF123',
  price: {
    total: 850,
    currency: 'USD',
  },
  duration: '8h 30m',
  stops: 0,
  cabin_class: 'economy',
};

global.mockHotelData = {
  id: 'hotel-123',
  name: 'Grand Hotel Paris',
  location: {
    address: '123 Rue de Rivoli, Paris',
    latitude: 48.8566,
    longitude: 2.3522,
  },
  check_in: '2024-06-01',
  check_out: '2024-06-08',
  room_type: 'Superior Double',
  price: {
    total: 1400,
    currency: 'USD',
    per_night: 200,
  },
  rating: 4.5,
  amenities: ['WiFi', 'Breakfast', 'Gym'],
};

// Console helpers for debugging tests
global.logTestState = (component: any) => {
  console.log('=== TEST STATE DEBUG ===');
  console.log('Component:', component);
  console.log('DOM:', component.container.innerHTML);
  console.log('======================');
};

// Async test helpers
global.waitForAsync = async (callback: () => void, timeout = 5000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const checkCondition = () => {
      try {
        callback();
        resolve(true);
      } catch (error) {
        if (Date.now() - startTime > timeout) {
          reject(new Error(`Timeout after ${timeout}ms: ${error}`));
        } else {
          setTimeout(checkCondition, 10);
        }
      }
    };
    checkCondition();
  });
};

// Network request helpers
global.mockApiResponse = (data: any, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => data,
  text: async () => JSON.stringify(data),
});

global.mockApiError = (status = 500, message = 'Internal Server Error') => ({
  ok: false,
  status,
  json: async () => ({ error: message }),
  text: async () => JSON.stringify({ error: message }),
});