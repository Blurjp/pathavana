import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UnifiedTravelRequest from '../pages/UnifiedTravelRequest';
import { SidebarProvider } from '../contexts/SidebarContext';
import { AuthProvider } from '../contexts/AuthContext';
import { unifiedTravelApi } from '../services/unifiedTravelApi';

// Mock dependencies
jest.mock('../services/unifiedTravelApi', () => ({
  unifiedTravelApi: {
    getSession: jest.fn(),
    sendChatMessage: jest.fn(),
    saveItemToTrip: jest.fn(),
    removeItemFromTrip: jest.fn(),
    exportSessionData: jest.fn()
  }
}));

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
  default: ({ type, status, count }: any) => (
    <div data-testid={`search-progress-${type}`}>
      {status === 'found' ? `Found ${count} ${type}s` : `Searching for ${type}s...`}
    </div>
  )
}));

// Mock hooks
const mockSendMessage = jest.fn();
const mockMessages: any[] = [];

jest.mock('../hooks/useUnifiedSession', () => ({
  useUnifiedSession: () => ({
    sessionId: 'test-session-123',
    messages: mockMessages,
    isMessageLoading: false,
    messageError: null,
    isStreaming: false,
    streamingMessage: null,
    sendMessage: mockSendMessage,
    createNewSession: jest.fn(),
    context: {
      currentRequest: {
        destination: null,
        departureDate: null,
        returnDate: null,
        travelers: 1
      }
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

// Mock chat response with trip plan intent
const mockChatResponseWithTripPlanIntent = {
  success: true,
  data: {
    message: "I'll help you create a trip plan to Paris! I've set up your trip plan for July 15-22, 2024. You can now search for flights, hotels, and activities to add to your itinerary.",
    updated_context: {
      destination: 'Paris',
      dates: { start: '2024-07-15', end: '2024-07-22' },
      travelers: 2
    },
    suggestions: ['Search for flights to Paris', 'Find hotels in Paris', 'Explore activities in Paris'],
    chat_history: [
      {
        id: 'msg-1',
        type: 'user',
        content: 'Create a trip plan for Paris from July 15-22 for 2 people',
        timestamp: new Date().toISOString()
      },
      {
        id: 'msg-2',
        type: 'assistant',
        content: "I'll help you create a trip plan to Paris! I've set up your trip plan for July 15-22, 2024. You can now search for flights, hotels, and activities to add to your itinerary.",
        timestamp: new Date().toISOString(),
        metadata: {
          should_create_trip_plan: true,
          trip_plan_intent: {
            wants_trip_plan: true,
            confidence: 0.95,
            reason: "User explicitly asked to 'create a trip plan'",
            trip_info: {
              destination_city: 'Paris',
              start_date: '2024-07-15',
              end_date: '2024-07-22',
              travelers: { adults: 2, children: 0, infants: 0 }
            }
          },
          trip_plan_created: true,
          trip_plan: {
            id: 'trip-123',
            name: 'Trip to Paris',
            destination: 'Paris',
            departure_date: '2024-07-15',
            return_date: '2024-07-22',
            travelers: 2,
            status: 'planning',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            saved_items: []
          }
        }
      }
    ]
  }
};

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

describe('Trip Plan Creation Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API calls
    (unifiedTravelApi.getSession as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session-123',
        status: 'active',
        session_data: {
          conversation_history: []
        },
        plan_data: {
          trip_context: {}
        }
      }
    });

    (unifiedTravelApi.sendChatMessage as jest.Mock).mockResolvedValue(mockChatResponseWithTripPlanIntent);
  });

  test('AI agent detects trip plan creation intent and creates trip automatically', async () => {
    renderWithProviders(<UnifiedTravelRequest />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Continue planning your trip\.\.\./i)).toBeInTheDocument();
    });

    // User sends message to create trip plan
    const input = screen.getByPlaceholderText(/Continue planning your trip\.\.\./i);
    fireEvent.change(input, { target: { value: 'Create a trip plan for Paris from July 15-22 for 2 people' } });
    
    // Find and click send button
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    // Wait for API call and response
    await waitFor(() => {
      expect(unifiedTravelApi.sendChatMessage).toHaveBeenCalledWith(
        'Create a trip plan for Paris from July 15-22 for 2 people',
        'test-session-123'
      );
    });

    // Wait for trip plan creation message
    await waitFor(() => {
      expect(screen.getByText(/I'll help you create a trip plan to Paris!/)).toBeInTheDocument();
    });

    // Verify sidebar opens automatically
    await waitFor(() => {
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toHaveClass('sidebar-open');
    });

    // Verify trip plan tab is visible
    expect(screen.getByRole('tab', { name: /trip plan/i })).toBeInTheDocument();
  });

  test('Trip plan shows correct information after creation', async () => {
    // Mock session with existing trip plan
    (unifiedTravelApi.getSession as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session-123',
        status: 'active',
        session_data: {
          conversation_history: mockChatResponseWithTripPlanIntent.data.chat_history
        },
        plan_data: {
          trip_context: {
            destination: 'Paris',
            dates: { start: '2024-07-15', end: '2024-07-22' },
            travelers: 2
          },
          trip: {
            id: 'trip-123',
            name: 'Trip to Paris',
            destination: 'Paris',
            departure_date: '2024-07-15',
            return_date: '2024-07-22',
            travelers: 2,
            status: 'planning',
            saved_items: []
          }
        }
      }
    });

    renderWithProviders(<UnifiedTravelRequest />);

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText(/I'll help you create a trip plan to Paris!/)).toBeInTheDocument();
    });

    // Click on trip plan tab
    const tripPlanTab = screen.getByRole('tab', { name: /trip plan/i });
    fireEvent.click(tripPlanTab);

    // Verify trip plan information is displayed
    await waitFor(() => {
      expect(screen.getByText(/Trip to Paris/)).toBeInTheDocument();
      expect(screen.getByText(/Jul 15 - Jul 22, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/2 travelers/)).toBeInTheDocument();
    });
  });

  test('Multiple trip plan creation intents are handled correctly', async () => {
    renderWithProviders(<UnifiedTravelRequest />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Continue planning your trip\.\.\./i)).toBeInTheDocument();
    });

    // First trip plan creation
    const input = screen.getByPlaceholderText(/Continue planning your trip\.\.\./i);
    fireEvent.change(input, { target: { value: 'Create a trip plan for Paris' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText(/I'll help you create a trip plan to Paris!/)).toBeInTheDocument();
    });

    // Try to create another trip plan - should not create duplicate
    fireEvent.change(input, { target: { value: 'Make another trip plan' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Should still only have one trip plan
    await waitFor(() => {
      const tripPlanMessages = screen.getAllByText(/I'll help you create a trip plan/);
      expect(tripPlanMessages).toHaveLength(1);
    });
  });

  test('Trip plan creation handles missing information gracefully', async () => {
    // Mock response with minimal trip info
    const minimalTripPlanResponse = {
      ...mockChatResponseWithTripPlanIntent,
      data: {
        ...mockChatResponseWithTripPlanIntent.data,
        chat_history: [
          {
            id: 'msg-1',
            type: 'user',
            content: 'I want to plan a trip',
            timestamp: new Date().toISOString()
          },
          {
            id: 'msg-2',
            type: 'assistant',
            content: "I'll help you plan your trip! Let me create a trip plan for you.",
            timestamp: new Date().toISOString(),
            metadata: {
              should_create_trip_plan: true,
              trip_plan_intent: {
                wants_trip_plan: true,
                confidence: 0.8,
                reason: "User expressed intent to plan a trip",
                trip_info: {}
              },
              trip_plan_created: true,
              trip_plan: {
                id: 'trip-456',
                name: 'Trip to Unknown',
                destination: 'Unknown',
                departure_date: null,
                return_date: null,
                travelers: 1,
                status: 'planning',
                saved_items: []
              }
            }
          }
        ]
      }
    };

    (unifiedTravelApi.sendChatMessage as jest.Mock).mockResolvedValue(minimalTripPlanResponse);

    renderWithProviders(<UnifiedTravelRequest />);

    // Send vague trip planning message
    const input = screen.getByPlaceholderText(/Continue planning your trip\.\.\./i);
    fireEvent.change(input, { target: { value: 'I want to plan a trip' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/I'll help you plan your trip!/)).toBeInTheDocument();
    });

    // Verify sidebar opens even with minimal info
    await waitFor(() => {
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toHaveClass('sidebar-open');
    });
  });

  test('Trip plan intent phrases trigger creation', async () => {
    const testPhrases = [
      'Create my trip plan to London',
      'Make a trip plan for next month',
      'Build my itinerary for Tokyo',
      'Start planning my vacation to Bali',
      'Help me plan a trip to Rome'
    ];

    for (const phrase of testPhrases) {
      // Clear mocks for each test
      jest.clearAllMocks();
      
      // Update mock response for each phrase
      const customResponse = {
        ...mockChatResponseWithTripPlanIntent,
        data: {
          ...mockChatResponseWithTripPlanIntent.data,
          chat_history: [
            {
              id: 'msg-1',
              type: 'user',
              content: phrase,
              timestamp: new Date().toISOString()
            },
            {
              id: 'msg-2',
              type: 'assistant',
              content: `I'll help you with that! Creating your trip plan now.`,
              timestamp: new Date().toISOString(),
              metadata: {
                should_create_trip_plan: true,
                trip_plan_intent: {
                  wants_trip_plan: true,
                  confidence: 0.95,
                  reason: `User explicitly asked to '${phrase}'`,
                  trip_info: {}
                },
                trip_plan_created: true,
                trip_plan: {
                  id: `trip-${Date.now()}`,
                  name: 'Your Trip',
                  destination: 'TBD',
                  status: 'planning',
                  saved_items: []
                }
              }
            }
          ]
        }
      };

      (unifiedTravelApi.sendChatMessage as jest.Mock).mockResolvedValue(customResponse);

      const { unmount } = renderWithProviders(<UnifiedTravelRequest />);

      // Send the test phrase
      const input = screen.getByPlaceholderText(/Continue planning your trip\.\.\./i);
      fireEvent.change(input, { target: { value: phrase } });
      fireEvent.click(screen.getByRole('button', { name: /send/i }));

      // Verify trip plan is created
      await waitFor(() => {
        expect(screen.getByText(/Creating your trip plan/i)).toBeInTheDocument();
      });

      // Clean up for next iteration
      unmount();
    }
  });
});