import { renderHook, act } from '@testing-library/react';
import { useConversationState } from './useConversationState';
import { ConversationState } from '../types/AIAgentTypes';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('useConversationState', () => {
  const sessionId = 'test-session-123';

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('should initialize with greeting state', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    expect(result.current.conversationState).toBe(ConversationState.GREETING);
    expect(result.current.context.state).toBe(ConversationState.GREETING);
    expect(result.current.messages).toHaveLength(0);
  });

  it('should load saved state from localStorage', () => {
    const savedState = {
      state: ConversationState.SEARCHING,
      context: {
        state: ConversationState.SEARCHING,
        entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      },
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Find flights to Tokyo',
          timestamp: new Date().toISOString(),
          metadata: {}
        }
      ]
    };

    localStorageMock.getItem.mockReturnValue(JSON.stringify(savedState));

    const { result } = renderHook(() => useConversationState(sessionId));

    expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
    expect(result.current.context.entities).toHaveLength(1);
    expect(result.current.messages).toHaveLength(1);
  });

  it('should add user message and extract intent/entities', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Find flights to Tokyo for 2 people',
        metadata: {}
      });
    });

    expect(result.current.messages).toHaveLength(1);
    const message = result.current.messages[0];
    
    expect(message.metadata.intent?.type).toBe('search_flight');
    expect(message.metadata.entities).toBeDefined();
    expect(message.metadata.entities?.some(e => e.type === 'destination')).toBe(true);
    expect(message.metadata.entities?.some(e => e.type === 'travelers')).toBe(true);
  });

  it('should transition conversation state based on intent', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Find flights to Tokyo on March 15 for 2 people',
        metadata: {}
      });
    });

    // Should transition from GREETING to SEARCHING (since all required fields are present)
    expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
  });

  it('should stay in gathering requirements if missing fields', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Find flights to Tokyo',
        metadata: {}
      });
    });

    // Should transition to GATHERING_REQUIREMENTS since dates and travelers are missing
    expect(result.current.conversationState).toBe(ConversationState.GATHERING_REQUIREMENTS);
  });

  it('should update context', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.updateContext({
        clarificationNeeded: true,
        missingFields: ['destination']
      });
    });

    expect(result.current.context.clarificationNeeded).toBe(true);
    expect(result.current.context.missingFields).toContain('destination');
  });

  it('should transition to specific state', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.transitionTo(ConversationState.BOOKING);
    });

    expect(result.current.conversationState).toBe(ConversationState.BOOKING);
    expect(result.current.context.state).toBe(ConversationState.BOOKING);
  });

  it('should clear conversation', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    // Add some messages first
    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Test message',
        metadata: {}
      });
      result.current.transitionTo(ConversationState.SEARCHING);
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

    // Clear conversation
    act(() => {
      result.current.clearConversation();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.conversationState).toBe(ConversationState.GREETING);
    expect(localStorageMock.removeItem).toHaveBeenCalledWith(`conversation-${sessionId}`);
  });

  it('should provide contextual quick actions', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    // Initial state should have greeting actions
    expect(result.current.quickActions).toEqual([
      { label: "Plan a trip", icon: "✈️", action: "start_planning" },
      { label: "View my plans", icon: "📋", action: "view_plans" },
      { label: "Check bookings", icon: "🎫", action: "view_bookings" }
    ]);

    // Transition to searching state
    act(() => {
      result.current.transitionTo(ConversationState.SEARCHING);
    });

    expect(result.current.quickActions).toEqual([
      { label: "Change dates", icon: "📅", action: "modify_dates" },
      { label: "Filter results", icon: "🔍", action: "add_filters" },
      { label: "Compare options", icon: "⚖️", action: "compare" }
    ]);
  });

  it('should save state to localStorage when it changes', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Test message',
        metadata: {}
      });
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      `conversation-${sessionId}`,
      expect.stringContaining('"messages"')
    );
  });

  it('should handle add to plan intent', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Add this to my plan',
        metadata: {}
      });
    });

    expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);
  });

  it('should handle view plan intent', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Show me my travel plan',
        metadata: {}
      });
    });

    expect(result.current.conversationState).toBe(ConversationState.REVIEWING_PLAN);
  });

  it('should handle booking intent', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Book this flight now',
        metadata: {}
      });
    });

    expect(result.current.conversationState).toBe(ConversationState.BOOKING);
  });

  it('should generate unique message IDs', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Message 1',
        metadata: {}
      });
      result.current.addMessage({
        role: 'user',
        content: 'Message 2',
        metadata: {}
      });
    });

    const ids = result.current.messages.map(m => m.id);
    expect(ids[0]).not.toBe(ids[1]);
    expect(ids[0]).toMatch(/^msg-\d+-[a-z0-9]+$/);
    expect(ids[1]).toMatch(/^msg-\d+-[a-z0-9]+$/);
  });

  it('should set timestamps on messages', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    const beforeTime = new Date();
    
    act(() => {
      result.current.addMessage({
        role: 'user',
        content: 'Test message',
        metadata: {}
      });
    });

    const afterTime = new Date();
    const messageTime = result.current.messages[0].timestamp;

    expect(messageTime.getTime()).toBeGreaterThanOrEqual(beforeTime.getTime());
    expect(messageTime.getTime()).toBeLessThanOrEqual(afterTime.getTime());
  });

  it('should limit saved messages to last 50', () => {
    const { result } = renderHook(() => useConversationState(sessionId));

    // Add 55 messages
    act(() => {
      for (let i = 0; i < 55; i++) {
        result.current.addMessage({
          role: 'user',
          content: `Message ${i}`,
          metadata: {}
        });
      }
    });

    expect(result.current.messages).toHaveLength(55);

    // Check that localStorage only saves last 50
    const savedData = JSON.parse(localStorageMock.setItem.mock.calls.slice(-1)[0][1]);
    expect(savedData.messages).toHaveLength(50);
    expect(savedData.messages[0].content).toBe('Message 5'); // First saved should be message 5
    expect(savedData.messages[49].content).toBe('Message 54'); // Last saved should be message 54
  });
});