/**
 * End-to-end conversation flow tests
 * Tests complete user journeys from greeting to booking
 */

import { renderHook, act } from '@testing-library/react';
import { useConversationState } from '../../hooks/useConversationState';
import { TravelAIService } from '../../services/AITravelService';
import { ConversationState } from '../../types/AIAgentTypes';

// Mock the API client
jest.mock('../../services/api', () => ({
  apiClient: {
    post: jest.fn(),
    put: jest.fn(),
    get: jest.fn()
  }
}));

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

describe('End-to-End Conversation Flows', () => {
  const sessionId = 'e2e-test-session';

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Complete Flight Booking Journey', () => {
    it('should handle complete flight search and booking flow', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: User greeting
      expect(result.current.conversationState).toBe(ConversationState.GREETING);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "Plan a trip", action: "start_planning" })
        ])
      );

      // Step 2: User expresses intent to travel
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'I want to plan a trip to Tokyo',
          metadata: {}
        });
      });

      // Should transition to gathering requirements due to missing info
      expect(result.current.conversationState).toBe(ConversationState.GATHERING_REQUIREMENTS);
      expect(result.current.context.missingFields).toContain('dates');
      expect(result.current.context.missingFields).toContain('travelers');

      // Step 3: User provides dates
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'I want to travel on March 15th',
          metadata: {}
        });
      });

      // Still gathering requirements (missing travelers)
      expect(result.current.conversationState).toBe(ConversationState.GATHERING_REQUIREMENTS);
      expect(result.current.context.missingFields).toContain('travelers');

      // Step 4: User provides traveler count
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'For 2 people',
          metadata: {}
        });
      });

      // Should now transition to searching
      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "Change dates", action: "modify_dates" }),
          expect.objectContaining({ label: "Filter results", action: "add_filters" })
        ])
      );

      // Step 5: Agent presents search results
      act(() => {
        result.current.addMessage({
          role: 'agent',
          content: 'I found some great flights for you!',
          metadata: {
            attachments: [{
              type: 'search_results',
              url: '',
              metadata: {
                type: 'card',
                cards: [{
                  title: 'ANA Flight NH101',
                  subtitle: 'JFK → NRT',
                  details: { Price: '$850', Duration: '14h 30m' },
                  actions: [
                    { label: 'Add to Plan', action: 'add_to_plan', data: {} }
                  ]
                }]
              }
            }]
          }
        });
      });

      // Should transition to presenting options
      expect(result.current.conversationState).toBe(ConversationState.PRESENTING_OPTIONS);

      // Step 6: User wants to add flight to plan
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Add this flight to my plan',
          metadata: {}
        });
      });

      // Should transition to adding to plan
      expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "View plan", action: "view_current_plan" })
        ])
      );

      // Step 7: User wants to view current plan
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Show me my travel plan',
          metadata: {}
        });
      });

      // Should transition to reviewing plan
      expect(result.current.conversationState).toBe(ConversationState.REVIEWING_PLAN);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "Book all", action: "book_all" })
        ])
      );

      // Step 8: User wants to book
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Book this flight now',
          metadata: {}
        });
      });

      // Should transition to booking
      expect(result.current.conversationState).toBe(ConversationState.BOOKING);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "Payment info", action: "payment_details" })
        ])
      );

      // Verify message count and content
      expect(result.current.messages).toHaveLength(8);
      expect(result.current.messages[0].content).toBe('I want to plan a trip to Tokyo');
      expect(result.current.messages[7].content).toBe('Book this flight now');
    });
  });

  describe('Hotel Search and Refinement Journey', () => {
    it('should handle hotel search with multiple refinements', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: User searches for hotels
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Find hotels in Tokyo for March 15th for 2 people',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

      // Step 2: Agent presents results
      act(() => {
        result.current.addMessage({
          role: 'agent',
          content: 'I found some hotels for you!',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.PRESENTING_OPTIONS);

      // Step 3: User wants to refine search (cheaper options)
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Show me something cheaper',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.REFINING_SEARCH);
      expect(result.current.quickActions).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ label: "Reset filters", action: "reset_filters" })
        ])
      );

      // Step 4: Second refinement (location preference)
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Near the airport would be better',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.REFINING_SEARCH);

      // Step 5: User satisfied with results
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Perfect! Add this hotel to my plan',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);
    });
  });

  describe('Multi-City Trip Planning Journey', () => {
    it('should handle complex multi-city trip planning', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: User wants to plan multi-city trip
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'I want to visit Tokyo and Kyoto in March for 2 people',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.GATHERING_REQUIREMENTS);

      // Step 2: Clarification needed for multiple destinations
      const context = result.current.context;
      expect(context.entities.some(e => e.type === 'destination')).toBe(true);

      // Step 3: User provides duration
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'For 10 days total',
          metadata: {}
        });
      });

      // Step 4: Search for flights
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Find flights to Tokyo first',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

      // Step 5: Add flights
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Add this flight to my plan',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);

      // Step 6: Search for hotels in Tokyo
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Now find hotels in Tokyo for 5 nights',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

      // Step 7: Plan Kyoto portion
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Also find trains from Tokyo to Kyoto',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
    });
  });

  describe('Error Recovery and Clarification Journey', () => {
    it('should handle ambiguous input and recover gracefully', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: Ambiguous request
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'I want to travel',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.GATHERING_REQUIREMENTS);
      expect(result.current.context.clarificationNeeded).toBe(true);

      // Step 2: Agent asks for clarification
      act(() => {
        result.current.addMessage({
          role: 'agent',
          content: 'Where would you like to travel to?',
          metadata: { actionRequired: true }
        });
      });

      // Step 3: User provides destination
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'To Paris',
          metadata: {}
        });
      });

      expect(result.current.context.entities.some(e => e.type === 'destination')).toBe(true);

      // Step 4: Still missing dates
      act(() => {
        result.current.addMessage({
          role: 'agent',
          content: 'When would you like to travel?',
          metadata: { actionRequired: true }
        });
      });

      // Step 5: User provides dates
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Next month',
          metadata: {}
        });
      });

      expect(result.current.context.entities.some(e => e.type === 'date')).toBe(true);

      // Step 6: Complete requirements gathering
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Just for myself',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
    });
  });

  describe('Recommendation and Discovery Journey', () => {
    it('should handle recommendation requests and activity planning', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: User asks for recommendations
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'What should I do in Tokyo?',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

      // Step 2: Agent provides recommendations
      act(() => {
        result.current.addMessage({
          role: 'agent',
          content: 'Here are some popular activities in Tokyo!',
          metadata: {
            attachments: [{
              type: 'activity_recommendations',
              url: '',
              metadata: {
                activities: [
                  { name: 'Senso-ji Temple', type: 'cultural' },
                  { name: 'Tokyo Food Tour', type: 'culinary' }
                ]
              }
            }]
          }
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.PRESENTING_OPTIONS);

      // Step 3: User shows interest in specific activity
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'The food tour sounds interesting. Tell me more',
          metadata: {}
        });
      });

      // Step 4: User adds activity to plan
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Add the food tour to my plan',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);

      // Step 5: Ask for more recommendations
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'What else do you recommend for families?',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);
    });
  });

  describe('Budget Management Journey', () => {
    it('should handle budget tracking and optimization', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Step 1: User sets budget
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'I have a budget of $3000 for my Tokyo trip',
          metadata: {}
        });
      });

      expect(result.current.context.entities.some(e => e.type === 'budget' && e.value === 3000)).toBe(true);

      // Step 2: Search with budget constraints
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Find flights and hotels within my budget',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.SEARCHING);

      // Step 3: Add items to plan
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Add this flight and hotel to my plan',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.ADDING_TO_PLAN);

      // Step 4: Check budget status
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'How much of my budget have I used?',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.REVIEWING_PLAN);

      // Step 5: Budget optimization request
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Can you find cheaper alternatives?',
          metadata: {}
        });
      });

      expect(result.current.conversationState).toBe(ConversationState.REFINING_SEARCH);
    });
  });

  describe('Session Persistence and Recovery', () => {
    it('should persist and restore conversation state', async () => {
      const { result, unmount } = renderHook(() => useConversationState(sessionId));

      // Add some messages
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Find flights to Tokyo',
          metadata: {}
        });
        result.current.transitionTo(ConversationState.SEARCHING);
      });

      const originalState = result.current.conversationState;
      const originalMessages = result.current.messages;

      // Verify localStorage was called
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        `conversation-${sessionId}`,
        expect.stringContaining('SEARCHING')
      );

      // Unmount and remount to simulate page refresh
      unmount();

      // Mock localStorage returning saved state
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        state: originalState,
        context: {
          state: originalState,
          entities: [],
          missingFields: [],
          lastIntent: null,
          clarificationNeeded: false
        },
        messages: originalMessages
      }));

      const { result: newResult } = renderHook(() => useConversationState(sessionId));

      // Should restore previous state
      expect(newResult.current.conversationState).toBe(originalState);
      expect(newResult.current.messages).toHaveLength(originalMessages.length);
    });

    it('should clear conversation when requested', async () => {
      const { result } = renderHook(() => useConversationState(sessionId));

      // Add messages and change state
      act(() => {
        result.current.addMessage({
          role: 'user',
          content: 'Test message',
          metadata: {}
        });
        result.current.transitionTo(ConversationState.BOOKING);
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.conversationState).toBe(ConversationState.BOOKING);

      // Clear conversation
      act(() => {
        result.current.clearConversation();
      });

      expect(result.current.messages).toHaveLength(0);
      expect(result.current.conversationState).toBe(ConversationState.GREETING);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(`conversation-${sessionId}`);
    });
  });

  describe('Error Scenarios', () => {
    it('should handle corrupted localStorage data gracefully', async () => {
      // Mock corrupted data
      localStorageMock.getItem.mockReturnValue('invalid json');

      const { result } = renderHook(() => useConversationState(sessionId));

      // Should start with default state
      expect(result.current.conversationState).toBe(ConversationState.GREETING);
      expect(result.current.messages).toHaveLength(0);
    });

    it('should handle missing localStorage gracefully', async () => {
      // Mock localStorage throwing error
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage not available');
      });

      const { result } = renderHook(() => useConversationState(sessionId));

      // Should still work with default state
      expect(result.current.conversationState).toBe(ConversationState.GREETING);
      expect(result.current.messages).toHaveLength(0);
    });
  });
});