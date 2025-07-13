/**
 * Integration tests for the AI Travel Agent system
 * Tests the complete flow from user input to AI response
 */

import { TravelNLUEngine } from '../../services/NLUEngine';
import { TravelConversationalSearch } from '../../services/ConversationalSearch';
import { TravelAIService } from '../../services/AITravelService';
import { 
  ConversationState, 
  EnhancedChatMessage, 
  UserPreferences,
  SearchResult,
  SearchContext
} from '../../types/AIAgentTypes';

// Mock the API client
jest.mock('../../services/api', () => ({
  apiClient: {
    post: jest.fn(),
    put: jest.fn(),
    get: jest.fn()
  }
}));

describe('AI Travel Agent Integration Tests', () => {
  let nluEngine: TravelNLUEngine;
  let conversationalSearch: TravelConversationalSearch;
  let aiService: TravelAIService;

  beforeEach(() => {
    nluEngine = new TravelNLUEngine();
    conversationalSearch = new TravelConversationalSearch();
    aiService = new TravelAIService();
    jest.clearAllMocks();
  });

  describe('Complete Conversation Flow', () => {
    it('should handle a complete flight search conversation', async () => {
      // Step 1: User wants to plan a trip
      const message1 = "I want to plan a trip to Tokyo";
      const intent1 = nluEngine.extractIntent(message1);
      const entities1 = nluEngine.extractEntities(message1);

      expect(intent1.type).toBe('search_flight');
      expect(entities1.some(e => e.type === 'destination')).toBe(true);

      // Step 2: User provides dates
      const message2 = "I want to travel on March 15th for a week";
      const intent2 = nluEngine.extractIntent(message2);
      const entities2 = nluEngine.extractEntities(message2);

      expect(entities2.some(e => e.type === 'date')).toBe(true);

      // Step 3: User provides traveler count
      const message3 = "For 2 people";
      const entities3 = nluEngine.extractEntities(message3);

      expect(entities3.some(e => e.type === 'travelers' && e.value === 2)).toBe(true);

      // Step 4: Context accumulation
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: message1,
          timestamp: new Date(),
          metadata: { intent: intent1, entities: entities1 }
        },
        {
          id: '2',
          role: 'user',
          content: message2,
          timestamp: new Date(),
          metadata: { intent: intent2, entities: entities2 }
        },
        {
          id: '3',
          role: 'user',
          content: message3,
          timestamp: new Date(),
          metadata: { entities: entities3 }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      
      // Should have all required information
      expect(context.entities.some(e => e.type === 'destination')).toBe(true);
      expect(context.entities.some(e => e.type === 'date')).toBe(true);
      expect(context.entities.some(e => e.type === 'travelers')).toBe(true);
      expect(context.missingFields.length).toBeLessThanOrEqual(1); // Budget might be missing
    });

    it('should handle search refinement flow', () => {
      // Initial search
      const initialQuery = {
        query: 'flights to Tokyo',
        filters: { maxPrice: 1000 },
        page: 1
      };

      // User wants cheaper options
      const refinedQuery = conversationalSearch.refineSearch(
        initialQuery,
        'Find me something cheaper'
      );

      expect(refinedQuery.filters.maxPrice).toBe(800); // 80% of original

      // User wants direct flights
      const refinedQuery2 = conversationalSearch.refineSearch(
        refinedQuery,
        'I prefer direct flights'
      );

      expect(refinedQuery2.filters.maxStops).toBe(0);
    });

    it('should format search results with personalization', () => {
      const searchResults: SearchResult[] = [
        {
          id: 'flight1',
          type: 'flight',
          data: {
            airline: 'Delta',
            departure: 'JFK',
            arrival: 'NRT',
            duration: '14h 30m',
            price: { amount: 850, currency: 'USD', displayPrice: '$850' },
            stops: 0
          },
          relevanceScore: 0.9
        },
        {
          id: 'hotel1',
          type: 'hotel',
          data: {
            name: 'Tokyo Grand Hotel',
            rating: 4,
            price: { amount: 200, currency: 'USD', displayPrice: '$200' },
            location: 'Shibuya',
            amenities: ['wifi', 'pool', 'gym'],
            reviewScore: 8.5,
            reviewCount: 1200
          },
          relevanceScore: 0.8
        }
      ];

      const preferences: UserPreferences = {
        preferredAirlines: ['Delta'],
        travelStyle: 'comfort'
      };

      const formatted = conversationalSearch.formatResults(searchResults, preferences);

      expect(formatted).toContain('✈️ **Flights:**');
      expect(formatted).toContain('🏨 **Hotels:**');
      expect(formatted).toContain('Delta');
      expect(formatted).toContain('Tokyo Grand Hotel');
      expect(formatted).toContain('⭐ Your preferred airline');
      expect(formatted).toContain('Direct flight for your comfort');
    });
  });

  describe('Intent Recognition Accuracy', () => {
    const testCases = [
      { input: "Find me flights to Paris", expectedIntent: "search_flight" },
      { input: "Book hotels in Tokyo", expectedIntent: "search_hotel" },
      { input: "Add this flight to my plan", expectedIntent: "add_to_plan" },
      { input: "Show me my travel plan", expectedIntent: "view_plan" },
      { input: "Book this now", expectedIntent: "book_item" },
      { input: "What should I do in Rome?", expectedIntent: "get_recommendations" },
      { input: "How much will this cost?", expectedIntent: "check_budget" }
    ];

    testCases.forEach(({ input, expectedIntent }) => {
      it(`should recognize intent "${expectedIntent}" from "${input}"`, () => {
        const intent = nluEngine.extractIntent(input);
        expect(intent.type).toBe(expectedIntent);
        expect(intent.confidence).toBeGreaterThan(0);
      });
    });
  });

  describe('Entity Extraction Accuracy', () => {
    it('should extract multiple destinations correctly', () => {
      const entities = nluEngine.extractEntities('I want to visit Tokyo and Kyoto');
      const destinations = entities.filter(e => e.type === 'destination');
      
      expect(destinations.length).toBeGreaterThanOrEqual(1);
      expect(destinations.some(d => d.value.includes('Tokyo'))).toBe(true);
    });

    it('should extract complex date patterns', () => {
      const testCases = [
        'Flying on March 15, 2024',
        'Departure tomorrow',
        'Travel next week',
        'Leave on Monday'
      ];

      testCases.forEach(text => {
        const entities = nluEngine.extractEntities(text);
        const dates = entities.filter(e => e.type === 'date');
        expect(dates.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should extract budget information accurately', () => {
      const testCases = [
        { text: 'Budget is $5000', expected: 5000 },
        { text: 'Around 2500 dollars', expected: 2500 },
        { text: 'Under $1000', expected: 1000 }
      ];

      testCases.forEach(({ text, expected }) => {
        const entities = nluEngine.extractEntities(text);
        const budgets = entities.filter(e => e.type === 'budget');
        expect(budgets.length).toBeGreaterThanOrEqual(1);
        expect(budgets[0].value).toBe(expected);
      });
    });

    it('should extract traveler information', () => {
      const testCases = [
        { text: '3 adults traveling', expected: 3 },
        { text: 'Party of 5', expected: 5 },
        { text: 'Solo trip', expected: 1 },
        { text: 'Couple vacation', expected: 2 }
      ];

      testCases.forEach(({ text, expected }) => {
        const entities = nluEngine.extractEntities(text);
        const travelers = entities.filter(e => e.type === 'travelers');
        expect(travelers.length).toBeGreaterThanOrEqual(1);
        expect(travelers[0].value).toBe(expected);
      });
    });
  });

  describe('Context Management', () => {
    it('should maintain context across multiple messages', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'I want to go to Tokyo',
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }]
          }
        },
        {
          id: '2',
          role: 'user',
          content: 'In March',
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'date', value: 'March', confidence: 0.8, position: [0, 5] }]
          }
        },
        {
          id: '3',
          role: 'user',
          content: 'For 2 people',
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'travelers', value: 2, confidence: 0.9, position: [0, 5] }]
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      
      expect(context.entities).toHaveLength(3);
      expect(context.entities.find(e => e.type === 'destination')?.value).toBe('Tokyo');
      expect(context.entities.find(e => e.type === 'date')?.value).toBe('March');
      expect(context.entities.find(e => e.type === 'travelers')?.value).toBe(2);
    });

    it('should identify missing required fields', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'Find flights to Tokyo',
          timestamp: new Date(),
          metadata: {
            intent: { type: 'search_flight', confidence: 0.9, parameters: {} },
            entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }]
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      
      expect(context.missingFields).toContain('dates');
      expect(context.missingFields).toContain('travelers');
      expect(context.clarificationNeeded).toBe(true);
    });

    it('should generate appropriate clarification questions', () => {
      const context = {
        state: ConversationState.GATHERING_REQUIREMENTS,
        entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }],
        missingFields: ['dates'],
        lastIntent: null,
        clarificationNeeded: true
      };

      const clarification = nluEngine.clarifyIntent('', context);
      
      expect(clarification.question).toContain('When would you like to travel');
      expect(clarification.type).toBe('open_ended');
    });
  });

  describe('Conversational Search Features', () => {
    it('should handle relative price queries', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: { maxPrice: 800 },
        userFeedback: []
      };

      const query = conversationalSearch.parseRelativeQuery('something cheaper', context);
      
      expect(query.filters.maxPrice).toBe(560); // 70% of 800
    });

    it('should handle time-based relative queries', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const queries = [
        { input: 'earlier flight', expected: 'morning' },
        { input: 'later flight', expected: 'evening' },
        { input: 'red-eye flight', expected: 'night' }
      ];

      queries.forEach(({ input, expected }) => {
        const query = conversationalSearch.parseRelativeQuery(input, context);
        expect(query.filters.departureTimeRange).toBe(expected);
      });
    });

    it('should handle location preferences', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const preferences = [
        { input: 'closer to downtown', expected: 'downtown' },
        { input: 'near the airport', expected: 'airport' },
        { input: 'by the beach', expected: 'beach' }
      ];

      preferences.forEach(({ input, expected }) => {
        const query = conversationalSearch.parseRelativeQuery(input, context);
        expect(query.filters.locationPreference).toBe(expected);
      });
    });

    it('should handle sorting preferences', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const sorts = [
        { input: 'cheapest first', expected: 'price_asc' },
        { input: 'best rated', expected: 'rating_desc' },
        { input: 'most popular', expected: 'popularity_desc' }
      ];

      sorts.forEach(({ input, expected }) => {
        const query = conversationalSearch.parseRelativeQuery(input, context);
        expect(query.sort).toBe(expected);
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle empty or invalid input gracefully', () => {
      const emptyIntent = nluEngine.extractIntent('');
      expect(emptyIntent.type).toBe('search_flight'); // Default fallback
      
      const emptyEntities = nluEngine.extractEntities('');
      expect(emptyEntities).toEqual([]);
    });

    it('should handle ambiguous input', () => {
      const intent = nluEngine.extractIntent('help me with travel');
      expect(intent.type).toBe('search_flight');
      expect(intent.confidence).toBeGreaterThanOrEqual(0.3);
    });

    it('should handle conflicting entities', () => {
      const entities = nluEngine.extractEntities('I want to go to Tokyo and Paris and London');
      const destinations = entities.filter(e => e.type === 'destination');
      
      // Should extract multiple destinations for clarification
      expect(destinations.length).toBeGreaterThanOrEqual(1);
    });

    it('should handle empty search results gracefully', () => {
      const emptyResults: SearchResult[] = [];
      const preferences: UserPreferences = {};
      
      const formatted = conversationalSearch.formatResults(emptyResults, preferences);
      
      expect(formatted).toContain("I couldn't find any options");
      expect(formatted).toContain("adjust the search parameters");
    });
  });

  describe('Performance and Scalability', () => {
    it('should process intent extraction efficiently', () => {
      const start = performance.now();
      
      // Process 100 messages
      for (let i = 0; i < 100; i++) {
        nluEngine.extractIntent(`Find flights to destination ${i}`);
      }
      
      const end = performance.now();
      const duration = end - start;
      
      // Should process 100 messages in under 100ms
      expect(duration).toBeLessThan(100);
    });

    it('should handle large conversation histories', () => {
      const messages: EnhancedChatMessage[] = [];
      
      // Create 50 messages
      for (let i = 0; i < 50; i++) {
        messages.push({
          id: `msg-${i}`,
          role: 'user',
          content: `Message ${i}`,
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'destination', value: `City${i}`, confidence: 0.8, position: [0, 5] }]
          }
        });
      }

      const start = performance.now();
      const context = nluEngine.maintainContext(messages);
      const end = performance.now();
      
      expect(context.entities.length).toBeGreaterThan(0);
      expect(end - start).toBeLessThan(50); // Should process quickly
    });
  });
});