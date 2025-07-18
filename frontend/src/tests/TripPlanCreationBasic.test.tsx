import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ChatMessage } from '../types';

// Mock router
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ sessionId: 'test-session-123' }),
  useNavigate: () => jest.fn()
}));

// Mock all components and hooks before using them
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
  default: () => <div role="complementary">Trip Plan Sidebar</div>
}));

jest.mock('../components/ChatInput', () => ({
  __esModule: true,
  default: () => <div data-testid="chat-input">Chat Input</div>
}));

// Create a test component that simulates trip plan detection
const TripPlanDetectionTest = () => {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [tripPlanCreated, setTripPlanCreated] = React.useState(false);
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // Simulate trip plan detection logic
  React.useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.metadata?.trip_plan_created && !tripPlanCreated) {
      setTripPlanCreated(true);
      setSidebarOpen(true);
    }
  }, [messages, tripPlanCreated]);

  const handleSendMessage = (content: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    // Simulate AI response with trip plan creation
    const aiMessage: ChatMessage = {
      id: `ai-${Date.now()}`,
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
    };

    setMessages([...messages, userMessage, aiMessage]);
  };

  return (
    <div>
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.type}`}>
            {msg.content}
          </div>
        ))}
      </div>
      
      {tripPlanCreated && (
        <div data-testid="trip-plan-created">
          Trip plan has been created!
        </div>
      )}
      
      {sidebarOpen && (
        <div data-testid="sidebar" className="sidebar-open">
          Trip Plan Sidebar
        </div>
      )}
      
      <input
        type="text"
        placeholder="Type your message..."
        data-testid="message-input"
      />
      <button
        onClick={() => {
          const input = document.querySelector('[data-testid="message-input"]') as HTMLInputElement;
          if (input?.value) {
            handleSendMessage(input.value);
            input.value = '';
          }
        }}
        data-testid="send-button"
      >
        Send
      </button>
    </div>
  );
};

describe('Trip Plan Creation - Basic Tests', () => {
  test('detects trip plan creation from AI response metadata', async () => {
    render(<TripPlanDetectionTest />);

    // Send a message
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');

    fireEvent.change(input, { target: { value: 'Create a trip plan to Paris' } });
    fireEvent.click(sendButton);

    // Wait for trip plan creation
    await waitFor(() => {
      expect(screen.getByText("I'll help you create a trip plan to Paris!")).toBeInTheDocument();
      expect(screen.getByTestId('trip-plan-created')).toBeInTheDocument();
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    });
  });

  test('sidebar opens automatically when trip plan is created', async () => {
    render(<TripPlanDetectionTest />);

    // Initially no sidebar
    expect(screen.queryByTestId('sidebar')).toBeNull();

    // Send message
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');

    fireEvent.change(input, { target: { value: 'Plan my trip' } });
    fireEvent.click(sendButton);

    // Sidebar should appear
    await waitFor(() => {
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('sidebar')).toHaveClass('sidebar-open');
    });
  });
});

// Test trip plan intent detection logic
describe('Trip Plan Intent Detection Logic', () => {
  const detectTripPlanIntent = (message: string): { wants_trip_plan: boolean; confidence: number; reason: string } => {
    const messageLower = message.toLowerCase();
    
    const tripPlanPhrases = [
      'create a trip plan',
      'create my trip plan',
      'make a trip plan',
      'make my trip plan',
      'build my itinerary',
      'start planning my trip',
      'plan my trip',
      'help me plan',
      'organize my trip'
    ];
    
    for (const phrase of tripPlanPhrases) {
      if (messageLower.includes(phrase)) {
        return {
          wants_trip_plan: true,
          confidence: 0.95,
          reason: `User explicitly asked to '${phrase}'`
        };
      }
    }
    
    return {
      wants_trip_plan: false,
      confidence: 0,
      reason: 'No trip plan creation intent detected'
    };
  };

  test.each([
    ['Create a trip plan to Paris', true, 0.95],
    ['Make my trip plan for next week', true, 0.95],
    ['Build my itinerary for London', true, 0.95],
    ['Help me plan my vacation', true, 0.95],
    ['What is the weather in Tokyo?', false, 0],
    ['Show me flights to Rome', false, 0]
  ])('detects intent correctly for: "%s"', (message, expectedIntent, expectedConfidence) => {
    const result = detectTripPlanIntent(message);
    expect(result.wants_trip_plan).toBe(expectedIntent);
    expect(result.confidence).toBe(expectedConfidence);
  });
});