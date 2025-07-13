/**
 * Comprehensive tests for the AI Travel Service
 * Tests API integration, response processing, and action execution
 */

import { TravelAIService } from '../../services/AITravelService';
import { apiClient } from '../../services/api';
import {
  EnhancedChatMessage,
  ConversationContext,
  ConversationState,
  Action,
  CardResponse,
  TextResponse
} from '../../types/AIAgentTypes';

// Mock the API client
jest.mock('../../services/api');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock NLU Engine
jest.mock('../../services/NLUEngine', () => ({
  TravelNLUEngine: jest.fn().mockImplementation(() => ({
    extractIntent: jest.fn().mockReturnValue({
      type: 'search_flight',
      confidence: 0.9,
      parameters: {}
    }),
    extractEntities: jest.fn().mockReturnValue([
      { type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }
    ])
  }))
}));

describe('TravelAIService', () => {
  let aiService: TravelAIService;
  const sessionId = 'test-session-123';

  beforeEach(() => {
    aiService = new TravelAIService();
    jest.clearAllMocks();
  });

  describe('processMessage', () => {
    it('should process a user message and return agent response', async () => {
      const message: EnhancedChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Find flights to Tokyo',
        timestamp: new Date(),
        metadata: {}
      };

      const mockResponse = {
        data: {
          response: 'I found some great flights to Tokyo for you!',
          searchResults: {
            flights: [
              {
                id: 'flight-1',
                airline: 'ANA',
                flightNumber: 'NH101',
                origin: { code: 'JFK', name: 'John F. Kennedy', city: 'New York' },
                destination: { code: 'NRT', name: 'Narita', city: 'Tokyo' },
                departureTime: '2024-03-15T10:00:00Z',
                arrivalTime: '2024-03-16T14:30:00Z',
                duration: '14h 30m',
                price: { amount: 850, currency: 'USD', displayPrice: '$850' },
                stops: 0
              }
            ]
          }
        }
      };

      mockedApiClient.post.mockResolvedValue(mockResponse);

      const response = await aiService.processMessage(message, sessionId);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        `/api/travel/sessions/${sessionId}/chat`,
        expect.objectContaining({
          message: 'Find flights to Tokyo',
          metadata: expect.objectContaining({
            intent: 'search_flight'
          })
        })
      );

      expect(response.type).toBe('card');
      const cardResponse = response as CardResponse;
      expect(cardResponse.cards).toHaveLength(1);
      expect(cardResponse.cards[0].title).toContain('ANA');
    });

    it('should handle text-only responses', async () => {
      const message: EnhancedChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
        metadata: {}
      };

      const mockResponse = {
        data: {
          response: 'Hello! How can I help you plan your trip today?'
        }
      };

      mockedApiClient.post.mockResolvedValue(mockResponse);

      const response = await aiService.processMessage(message, sessionId);

      expect(response.type).toBe('text');
      const textResponse = response as TextResponse;
      expect(textResponse.content).toBe('Hello! How can I help you plan your trip today?');
    });

    it('should handle clarification requests', async () => {
      const message: EnhancedChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'I want to travel',
        timestamp: new Date(),
        metadata: {}
      };

      const mockResponse = {
        data: {
          clarificationNeeded: true,
          clarificationQuestion: 'Where would you like to travel to?'
        }
      };

      mockedApiClient.post.mockResolvedValue(mockResponse);

      const response = await aiService.processMessage(message, sessionId);

      expect(response.type).toBe('text');
      const textResponse = response as TextResponse;
      expect(textResponse.content).toBe('Where would you like to travel to?');
    });

    it('should handle API errors gracefully', async () => {
      const message: EnhancedChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Find flights',
        timestamp: new Date(),
        metadata: {}
      };

      mockedApiClient.post.mockRejectedValue(new Error('API Error'));

      const response = await aiService.processMessage(message, sessionId);

      expect(response.type).toBe('text');
      const textResponse = response as TextResponse;
      expect(textResponse.content).toContain('error processing your request');
    });
  });

  describe('updateContext', () => {
    it('should update session context locally and remotely', async () => {
      const context: ConversationContext = {
        state: ConversationState.SEARCHING,
        entities: [
          { type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }
        ],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      mockedApiClient.put.mockResolvedValue({ data: { success: true } });

      await aiService.updateContext(sessionId, context);

      expect(mockedApiClient.put).toHaveBeenCalledWith(
        `/api/travel/sessions/${sessionId}/context`,
        {
          context: {
            state: ConversationState.SEARCHING,
            entities: context.entities,
            missingFields: []
          }
        }
      );
    });

    it('should handle context update errors gracefully', async () => {
      const context: ConversationContext = {
        state: ConversationState.SEARCHING,
        entities: [],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      mockedApiClient.put.mockRejectedValue(new Error('Network error'));

      // Should not throw
      await expect(aiService.updateContext(sessionId, context)).resolves.not.toThrow();
    });
  });

  describe('executeAction', () => {
    const context: ConversationContext = {
      state: ConversationState.SEARCHING,
      entities: [],
      missingFields: [],
      lastIntent: null,
      clarificationNeeded: false
    };

    it('should execute add_to_plan action', async () => {
      const action: Action = {
        type: 'add_to_plan',
        payload: {
          type: 'flight',
          item: { id: 'flight-1', airline: 'ANA' }
        }
      };

      mockedApiClient.post.mockResolvedValue({
        data: { success: true, planId: 'plan-123' }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/travel/plan/items',
        action.payload
      );
    });

    it('should execute search action', async () => {
      const action: Action = {
        type: 'search',
        payload: {
          query: 'hotels in Tokyo',
          filters: { maxPrice: 200 },
          page: 1
        }
      };

      mockedApiClient.post.mockResolvedValue({
        data: {
          hotels: [
            { id: 'hotel-1', name: 'Tokyo Grand Hotel' }
          ]
        }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/travel/search',
        expect.objectContaining({
          query: 'hotels in Tokyo',
          filters: { maxPrice: 200 }
        })
      );
    });

    it('should execute search with refinement', async () => {
      const action: Action = {
        type: 'search',
        payload: {
          query: 'flights to Tokyo',
          filters: { maxPrice: 1000 },
          isRefinement: true,
          userFeedback: 'something cheaper'
        }
      };

      mockedApiClient.post.mockResolvedValue({
        data: { flights: [] }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/travel/search',
        expect.objectContaining({
          filters: expect.objectContaining({
            maxPrice: 800 // Should be refined to 80% of original
          })
        })
      );
    });

    it('should execute book action', async () => {
      const action: Action = {
        type: 'book',
        payload: {
          items: [{ id: 'flight-1', type: 'flight' }],
          paymentInfo: { method: 'card', details: {} }
        }
      };

      mockedApiClient.post.mockResolvedValue({
        data: {
          success: true,
          bookingReferences: ['REF123'],
          totalCost: 850
        }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(result.data.bookingReferences).toContain('REF123');
    });

    it('should execute modify_plan action', async () => {
      const action: Action = {
        type: 'modify_plan',
        payload: {
          planId: 'plan-123',
          changes: { removeItem: 'flight-1' }
        }
      };

      mockedApiClient.put.mockResolvedValue({
        data: { success: true, updatedPlan: {} }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(mockedApiClient.put).toHaveBeenCalledWith(
        '/api/travel/plan/plan-123',
        { removeItem: 'flight-1' }
      );
    });

    it('should execute get_recommendations action', async () => {
      const action: Action = {
        type: 'get_recommendations',
        payload: {
          destination: 'Tokyo',
          type: 'activities',
          preferences: { interests: ['culture', 'food'] }
        }
      };

      mockedApiClient.get.mockResolvedValue({
        data: {
          recommendations: [
            { id: 'act-1', name: 'Senso-ji Temple' }
          ]
        }
      });

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(true);
      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/travel/recommendations',
        {
          params: {
            destination: 'Tokyo',
            type: 'activities',
            preferences: JSON.stringify({ interests: ['culture', 'food'] })
          }
        }
      );
    });

    it('should handle unknown action types', async () => {
      const action: Action = {
        type: 'unknown_action',
        payload: {}
      };

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Unknown action type');
    });

    it('should handle action execution errors', async () => {
      const action: Action = {
        type: 'search',
        payload: { query: 'test' }
      };

      mockedApiClient.post.mockRejectedValue(new Error('API Error'));

      const result = await aiService.executeAction(action, context);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to perform search');
    });
  });

  describe('createCardResponse', () => {
    it('should create card response from flight results', () => {
      const searchResults = {
        flights: [
          {
            id: 'flight-1',
            airline: 'ANA',
            flightNumber: 'NH101',
            origin: { city: 'New York' },
            destination: { city: 'Tokyo' },
            departureTime: '2024-03-15T10:00:00Z',
            arrivalTime: '2024-03-16T14:30:00Z',
            duration: '14h 30m',
            price: { displayPrice: '$850' },
            stops: 0
          }
        ]
      };

      const context: ConversationContext = {
        state: ConversationState.PRESENTING_OPTIONS,
        entities: [],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      // Use private method via any cast for testing
      const cardResponse = (aiService as any).createCardResponse(searchResults, context);

      expect(cardResponse.type).toBe('card');
      expect(cardResponse.cards).toHaveLength(1);
      
      const card = cardResponse.cards[0];
      expect(card.title).toBe('ANA - NH101');
      expect(card.subtitle).toBe('New York → Tokyo');
      expect(card.details.Price).toBe('$850');
      expect(card.details.Stops).toBe('Non-stop');
      
      expect(card.actions).toHaveLength(2);
      expect(card.actions[0].label).toBe('Add to Plan');
      expect(card.actions[0].action).toBe('add_to_plan');
    });

    it('should create card response from hotel results', () => {
      const searchResults = {
        hotels: [
          {
            id: 'hotel-1',
            name: 'Tokyo Grand Hotel',
            rating: 4,
            location: { city: 'Tokyo', address: '123 Shibuya' },
            price: { displayPrice: '$200' },
            reviewScore: 8.5,
            reviewCount: 1200,
            amenities: ['wifi', 'pool', 'gym'],
            images: ['hotel1.jpg']
          }
        ]
      };

      const context: ConversationContext = {
        state: ConversationState.PRESENTING_OPTIONS,
        entities: [],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      const cardResponse = (aiService as any).createCardResponse(searchResults, context);

      expect(cardResponse.type).toBe('card');
      expect(cardResponse.cards).toHaveLength(1);
      
      const card = cardResponse.cards[0];
      expect(card.title).toBe('Tokyo Grand Hotel');
      expect(card.subtitle).toBe('Tokyo - 4★');
      expect(card.details.Price).toBe('$200/night');
      expect(card.details.Location).toBe('123 Shibuya');
      expect(card.details.Rating).toBe('8.5/10 (1200 reviews)');
    });

    it('should create card response from activity results', () => {
      const searchResults = {
        activities: [
          {
            id: 'activity-1',
            name: 'Tokyo Food Tour',
            type: 'food',
            location: { address: 'Shibuya District' },
            price: { displayPrice: '$75' },
            duration: '3 hours',
            rating: 4.8,
            images: ['tour1.jpg']
          }
        ]
      };

      const context: ConversationContext = {
        state: ConversationState.PRESENTING_OPTIONS,
        entities: [],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      const cardResponse = (aiService as any).createCardResponse(searchResults, context);

      expect(cardResponse.type).toBe('card');
      expect(cardResponse.cards).toHaveLength(1);
      
      const card = cardResponse.cards[0];
      expect(card.title).toBe('Tokyo Food Tour');
      expect(card.subtitle).toBe('food');
      expect(card.details.Price).toBe('$75');
      expect(card.details.Duration).toBe('3 hours');
      expect(card.details.Rating).toBe('4.8/5');
    });
  });

  describe('streamMessage', () => {
    it('should handle streaming messages via Server-Sent Events', (done) => {
      const message = 'Find flights to Tokyo';
      const chunks: string[] = [];

      // Mock EventSource
      const mockEventSource = {
        onmessage: null as any,
        onerror: null as any,
        addEventListener: jest.fn(),
        close: jest.fn()
      };

      // Mock EventSource constructor
      (global as any).EventSource = jest.fn(() => mockEventSource);

      const onChunk = (chunk: string) => {
        chunks.push(chunk);
      };

      const streamPromise = aiService.streamMessage(message, sessionId, onChunk);

      // Simulate streaming chunks
      setTimeout(() => {
        mockEventSource.onmessage({ data: JSON.stringify({ chunk: 'I found' }) });
        mockEventSource.onmessage({ data: JSON.stringify({ chunk: ' some great' }) });
        mockEventSource.onmessage({ data: JSON.stringify({ chunk: ' flights!' }) });
        
        // Simulate completion
        mockEventSource.addEventListener.mock.calls.find(
          call => call[0] === 'complete'
        )?.[1]();
      }, 10);

      streamPromise.then(() => {
        expect(chunks).toEqual(['I found', ' some great', ' flights!']);
        expect(mockEventSource.close).toHaveBeenCalled();
        done();
      });
    });

    it('should handle streaming errors gracefully', (done) => {
      const message = 'Test message';
      
      const mockEventSource = {
        onmessage: null as any,
        onerror: null as any,
        addEventListener: jest.fn(),
        close: jest.fn()
      };

      (global as any).EventSource = jest.fn(() => mockEventSource);

      const onChunk = jest.fn();
      const streamPromise = aiService.streamMessage(message, sessionId, onChunk);

      // Simulate error
      setTimeout(() => {
        mockEventSource.onerror();
      }, 10);

      streamPromise.then(() => {
        expect(mockEventSource.close).toHaveBeenCalled();
        done();
      });
    });
  });

  describe('formatDateTime', () => {
    it('should format datetime strings correctly', () => {
      const dateTime = '2024-03-15T10:30:00Z';
      const formatted = (aiService as any).formatDateTime(dateTime);
      
      expect(formatted).toMatch(/Mar \d{1,2}, \d{1,2}:\d{2} (AM|PM)/);
    });
  });
});