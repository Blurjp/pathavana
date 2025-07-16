import { TravelNLUEngine } from './NLUEngine';
import { EnhancedChatMessage, ConversationState } from '../types/AIAgentTypes';

describe('TravelNLUEngine', () => {
  let nluEngine: TravelNLUEngine;

  beforeEach(() => {
    nluEngine = new TravelNLUEngine();
  });

  describe('extractIntent', () => {
    it('should detect flight search intent', () => {
      const testCases = [
        'Find me flights to Tokyo',
        'I want to fly to Paris',
        'Show me airfare to London',
        'Book a flight from NYC to LA',
        'Looking for flights to Miami'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('search_flight');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect hotel search intent', () => {
      const testCases = [
        'Find hotels in Tokyo',
        'I need a place to stay in Paris',
        'Show me accommodation near Times Square',
        'Looking for lodging in Miami',
        'Book a hotel for my trip'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('search_hotel');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect add to plan intent', () => {
      const testCases = [
        'Add this to my plan',
        'I\'ll take this one',
        'Save this for later',
        'Include it in my itinerary',
        'Add to my trip'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('add_to_plan');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect view plan intent', () => {
      const testCases = [
        'Show me my travel plan',
        'What\'s in my itinerary?',
        'View my current plan',
        'Check my trip so far',
        'Display my bookings'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('view_plan');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect booking intent', () => {
      const testCases = [
        'Book this now',
        'Confirm my reservation',
        'I\'m ready to book',
        'Proceed with booking',
        'Purchase these tickets'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('book_item');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect recommendation intent', () => {
      const testCases = [
        'What should I do in Tokyo?',
        'Recommend restaurants in Paris',
        'What are the must-see places?',
        'Suggest activities for families',
        'What\'s popular in Miami?'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('get_recommendations');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should detect budget check intent', () => {
      const testCases = [
        'How much will this cost?',
        'What\'s my total budget?',
        'Can I afford this?',
        'Show me the expenses',
        'Is this within my budget?'
      ];

      testCases.forEach(message => {
        const intent = nluEngine.extractIntent(message);
        expect(intent.type).toBe('check_budget');
        expect(intent.confidence).toBeGreaterThan(0.5);
      });
    });

    it('should default to search_flight for ambiguous travel messages', () => {
      const intent = nluEngine.extractIntent('I want to travel next month');
      expect(intent.type).toBe('search_flight');
      expect(intent.confidence).toBeLessThan(0.5);
    });
  });

  describe('extractEntities', () => {
    it('should extract destination entities', () => {
      const entities = nluEngine.extractEntities('I want to fly to Tokyo and visit Kyoto');
      const destinations = entities.filter(e => e.type === 'destination');
      
      expect(destinations).toHaveLength(2);
      expect(destinations[0].value).toBe('Tokyo');
      expect(destinations[1].value).toBe('Kyoto');
    });

    it('should extract date entities', () => {
      const entities = nluEngine.extractEntities('Flying on March 15, 2024 and returning March 22');
      const dates = entities.filter(e => e.type === 'date');
      
      expect(dates).toHaveLength(2);
      expect(dates[0].value).toContain('March 15');
      expect(dates[1].value).toContain('March 22');
    });

    it('should extract relative date entities', () => {
      const entities = nluEngine.extractEntities('I want to travel next week');
      const dates = entities.filter(e => e.type === 'date');
      
      expect(dates).toHaveLength(1);
      expect(dates[0].value).toBe('next week');
    });

    it('should extract budget entities', () => {
      const testCases = [
        { text: 'My budget is $3000', expected: 3000 },
        { text: 'I have 2,500 dollars to spend', expected: 2500 },
        { text: 'Keep it under $1000', expected: 1000 }
      ];

      testCases.forEach(({ text, expected }) => {
        const entities = nluEngine.extractEntities(text);
        const budgets = entities.filter(e => e.type === 'budget');
        
        expect(budgets).toHaveLength(1);
        expect(budgets[0].value).toBe(expected);
      });
    });

    it('should extract traveler count entities', () => {
      const testCases = [
        { text: '2 adults traveling', expected: 2 },
        { text: 'Party of 4', expected: 4 },
        { text: 'Just myself', expected: 1 },
        { text: 'Traveling as a couple', expected: 2 },
        { text: 'Family trip', expected: 4 }
      ];

      testCases.forEach(({ text, expected }) => {
        const entities = nluEngine.extractEntities(text);
        const travelers = entities.filter(e => e.type === 'travelers');
        
        expect(travelers).toHaveLength(1);
        expect(travelers[0].value).toBe(expected);
      });
    });

    it('should extract preference entities', () => {
      const entities = nluEngine.extractEntities('I prefer luxury hotels with direct flights in business class');
      const preferences = entities.filter(e => e.type === 'preference');
      
      expect(preferences.map(p => p.value)).toContain('luxury');
      expect(preferences.map(p => p.value)).toContain('direct');
      expect(preferences.map(p => p.value)).toContain('business class');
    });

    it('should deduplicate entities', () => {
      const entities = nluEngine.extractEntities('Tokyo to Tokyo flights');
      const destinations = entities.filter(e => e.type === 'destination');
      
      expect(destinations).toHaveLength(1);
      expect(destinations[0].value).toBe('Tokyo');
    });

    it('should include position information', () => {
      const entities = nluEngine.extractEntities('Flying to Paris');
      const destinations = entities.filter(e => e.type === 'destination');
      
      expect(destinations[0].position).toBeDefined();
      expect(destinations[0].position[0]).toBeGreaterThanOrEqual(0);
      expect(destinations[0].position[1]).toBeGreaterThan(destinations[0].position[0]);
    });
  });

  describe('maintainContext', () => {
    it('should determine conversation state from messages', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'Find flights to Tokyo',
          timestamp: new Date(),
          metadata: {
            intent: { type: 'search_flight', confidence: 0.9, parameters: {} }
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      expect(context.state).toBe(ConversationState.SEARCHING);
    });

    it('should accumulate entities from multiple messages', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'I want to go to Tokyo',
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 0] }]
          }
        },
        {
          id: '2',
          role: 'user',
          content: 'For 2 people',
          timestamp: new Date(),
          metadata: {
            entities: [{ type: 'travelers', value: 2, confidence: 0.9, position: [0, 0] }]
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      expect(context.entities).toHaveLength(2);
      expect(context.entities.find(e => e.type === 'destination')?.value).toBe('Tokyo');
      expect(context.entities.find(e => e.type === 'travelers')?.value).toBe(2);
    });

    it('should identify missing fields for flight search', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'Find flights to Tokyo',
          timestamp: new Date(),
          metadata: {
            intent: { type: 'search_flight', confidence: 0.9, parameters: {} },
            entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 0] }]
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      expect(context.missingFields).toContain('dates');
      expect(context.missingFields).toContain('travelers');
      expect(context.clarificationNeeded).toBe(true);
    });

    it('should detect no clarification needed when all fields present', () => {
      const messages: EnhancedChatMessage[] = [
        {
          id: '1',
          role: 'user',
          content: 'Find flights to Tokyo on March 15 for 2 people',
          timestamp: new Date(),
          metadata: {
            intent: { type: 'search_flight', confidence: 0.9, parameters: {} },
            entities: [
              { type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 0] as [number, number] },
              { type: 'date' as const, value: 'March 15', confidence: 0.9, position: [0, 0] as [number, number] },
              { type: 'travelers', value: 2, confidence: 0.9, position: [0, 0] }
            ]
          }
        }
      ];

      const context = nluEngine.maintainContext(messages);
      expect(context.missingFields).toHaveLength(0);
      expect(context.clarificationNeeded).toBe(false);
    });
  });

  describe('clarifyIntent', () => {
    it('should ask for destination when missing', () => {
      const context = {
        state: ConversationState.GATHERING_REQUIREMENTS,
        entities: [],
        missingFields: ['destination'],
        lastIntent: null,
        clarificationNeeded: true
      };

      const clarification = nluEngine.clarifyIntent('', context);
      expect(clarification.question).toContain('Where would you like to travel');
      expect(clarification.type).toBe('open_ended');
    });

    it('should ask for dates when missing', () => {
      const context = {
        state: ConversationState.GATHERING_REQUIREMENTS,
        entities: [{ type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 0] as [number, number] }],
        missingFields: ['dates'],
        lastIntent: null,
        clarificationNeeded: true
      };

      const clarification = nluEngine.clarifyIntent('', context);
      expect(clarification.question).toContain('When would you like to travel');
      expect(clarification.type).toBe('open_ended');
    });

    it('should ask for traveler count when missing', () => {
      const context = {
        state: ConversationState.GATHERING_REQUIREMENTS,
        entities: [
          { type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 0] as [number, number] },
          { type: 'date' as const, value: 'March 15', confidence: 0.9, position: [0, 0] as [number, number] }
        ],
        missingFields: ['travelers'],
        lastIntent: null,
        clarificationNeeded: true
      };

      const clarification = nluEngine.clarifyIntent('', context);
      expect(clarification.question).toContain('How many people');
      expect(clarification.type).toBe('single_choice');
      expect(clarification.options).toBeDefined();
    });

    it('should handle multiple destinations ambiguity', () => {
      const context = {
        state: ConversationState.GATHERING_REQUIREMENTS,
        entities: [
          { type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 0] as [number, number] },
          { type: 'destination' as const, value: 'Kyoto', confidence: 0.9, position: [0, 0] as [number, number] }
        ],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: true
      };

      const clarification = nluEngine.clarifyIntent('', context);
      expect(clarification.question).toContain('multiple destinations');
      expect(clarification.type).toBe('single_choice');
      expect(clarification.options).toContain('Tokyo');
      expect(clarification.options).toContain('Kyoto');
    });
  });
});