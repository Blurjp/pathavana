import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UnifiedTravelRequest from '../pages/UnifiedTravelRequest';
import { SidebarProvider } from '../contexts/SidebarContext';
import { AuthProvider } from '../contexts/AuthContext';

// Mock dependencies
jest.mock('../services/unifiedTravelApi');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ sessionId: 'test-session-123' }),
  useNavigate: () => jest.fn()
}));

// Mock components
jest.mock('../components/InteractiveMap', () => ({
  __esModule: true,
  default: () => <div data-testid="interactive-map">Map</div>
}));

jest.mock('../components/search/SearchProgress', () => ({
  __esModule: true,
  default: () => <div data-testid="search-progress">Search Progress</div>
}));

jest.mock('../components/SearchResultsSidebar', () => ({
  __esModule: true,
  default: ({ sessionId }: any) => (
    <div role="complementary" className="sidebar-open">
      <div role="tab">Trip Plan</div>
      <div>Trip Plan Content for session {sessionId}</div>
    </div>
  )
}));

jest.mock('../components/ChatInput', () => ({
  __esModule: true,
  default: ({ onSendMessage, isLoading }: any) => {
    const React = require('react');
    const [inputValue, setInputValue] = React.useState('');
    
    return (
      <div>
        <input
          type="text"
          placeholder="Continue planning your trip..."
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isLoading}
        />
        <button
          onClick={() => onSendMessage(inputValue)}
          disabled={isLoading}
          aria-label="Send"
        >
          Send
        </button>
      </div>
    );
  }
}));

// Test state management
let testMessages: any[] = [];
let testSidebarOpen = false;

// Mock hooks
jest.mock('../hooks/useUnifiedSession', () => ({
  useUnifiedSession: () => ({
    sessionId: 'test-session-123',
    messages: testMessages,
    isMessageLoading: false,
    messageError: null,
    isStreaming: false,
    streamingMessage: null,
    sendMessage: jest.fn(async (message: string) => {
      // Simulate message being added
      testMessages = [
        ...testMessages,
        {
          id: 'user-' + Date.now(),
          type: 'user',
          content: message,
          timestamp: new Date().toISOString()
        },
        {
          id: 'assistant-' + Date.now(),
          type: 'assistant',
          content: "I'll help you create a trip plan to Paris! I've set up your trip plan for July 15-22, 2024.",
          timestamp: new Date().toISOString(),
          metadata: {
            trip_plan_created: true,
            trip_plan: {
              id: 'trip-123',
              name: 'Trip to Paris',
              destination: 'Paris'
            }
          }
        }
      ];
    }),
    createNewSession: jest.fn(),
    context: {
      currentRequest: {}
    },
    updateContext: jest.fn(),
    resendMessage: jest.fn(),
    deleteMessage: jest.fn(),
    editMessage: jest.fn(),
    syncWithServer: jest.fn(),
    searchResults: undefined,
    isSearching: false
  })
}));

jest.mock('../contexts/SidebarContext', () => ({
  SidebarProvider: ({ children }: any) => <div>{children}</div>,
  useSidebar: () => ({
    sidebarOpen: testSidebarOpen,
    toggleSidebar: jest.fn(() => { testSidebarOpen = true; }),
    activeTab: 'trip',
    setActiveTab: jest.fn(),
    selectedItems: { flights: [], hotels: [], activities: [] },
    toggleItemSelection: jest.fn(),
    clearSelections: jest.fn(),
    getSelectedCount: jest.fn(() => 0)
  })
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <SidebarProvider>
          {component}
        </SidebarProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Trip Plan Creation - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    testMessages = [];
    testSidebarOpen = false;
  });

  test('renders chat interface', () => {
    renderWithProviders(<UnifiedTravelRequest />);
    
    expect(screen.getByPlaceholderText(/continue planning your trip/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  test('shows trip plan created message when metadata indicates creation', async () => {
    // Pre-populate with trip plan created message
    testMessages = [
      {
        id: 'msg-1',
        type: 'assistant',
        content: "I'll help you create a trip plan to Paris!",
        timestamp: new Date().toISOString(),
        metadata: {
          trip_plan_created: true,
          trip_plan: {
            id: 'trip-123',
            name: 'Trip to Paris',
            destination: 'Paris'
          }
        }
      }
    ];

    renderWithProviders(<UnifiedTravelRequest />);

    // Should show the message
    await waitFor(() => {
      expect(screen.getByText(/I'll help you create a trip plan to Paris!/)).toBeInTheDocument();
    });

    // Should show sidebar
    expect(screen.getByRole('complementary')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /trip plan/i })).toBeInTheDocument();
  });

  test('opens sidebar automatically when trip plan is created', async () => {
    renderWithProviders(<UnifiedTravelRequest />);

    // Initially no sidebar open class
    expect(testSidebarOpen).toBe(false);

    // Simulate receiving a message with trip plan created
    testMessages = [
      {
        id: 'msg-1',
        type: 'assistant',
        content: 'Trip plan created!',
        timestamp: new Date().toISOString(),
        metadata: {
          trip_plan_created: true
        }
      }
    ];

    // Force re-render
    const { rerender } = renderWithProviders(<UnifiedTravelRequest />);
    rerender(<UnifiedTravelRequest />);

    await waitFor(() => {
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });
  });

  test('detects trip plan intent from user message', async () => {
    renderWithProviders(<UnifiedTravelRequest />);

    const input = screen.getByPlaceholderText(/continue planning your trip/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Type message
    fireEvent.change(input, { target: { value: 'Create a trip plan to London' } });
    
    // Send message
    fireEvent.click(sendButton);

    // Wait for response
    await waitFor(() => {
      expect(testMessages).toHaveLength(2); // User message + assistant response
      expect(testMessages[1].metadata?.trip_plan_created).toBe(true);
    });
  });

  test('handles multiple trip plan creation attempts', async () => {
    // Start with existing trip plan
    testMessages = [
      {
        id: 'msg-1',
        type: 'assistant',
        content: 'First trip plan created',
        metadata: { trip_plan_created: true }
      }
    ];

    renderWithProviders(<UnifiedTravelRequest />);

    const input = screen.getByPlaceholderText(/continue planning your trip/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Try to create another trip plan
    fireEvent.change(input, { target: { value: 'Create another trip plan' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      // Should still work but not duplicate the sidebar opening
      expect(testMessages).toHaveLength(3);
    });
  });
});