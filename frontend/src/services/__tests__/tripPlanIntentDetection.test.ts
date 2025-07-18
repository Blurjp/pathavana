import { unifiedTravelApi } from '../unifiedTravelApi';
import { apiClient } from '../api';

jest.mock('../api');

describe('Trip Plan Intent Detection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Backend AI Intent Detection', () => {
    test('detects explicit trip plan creation requests', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I'll create your trip plan to Paris!",
          updated_context: { destination: 'Paris' },
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.95,
              reason: "User explicitly asked to 'create a trip plan'",
              trip_info: { destination_city: 'Paris' }
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'Create a trip plan to Paris for next week',
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(true);
      expect(result.data?.metadata?.trip_plan_intent?.confidence).toBeGreaterThan(0.9);
    });

    test('detects implicit trip planning intent with destination and dates', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I'll help you plan your trip to Tokyo!",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.8,
              reason: "User provided destination and dates with planning context",
              trip_info: {
                destination_city: 'Tokyo',
                start_date: '2024-08-01',
                end_date: '2024-08-10'
              }
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'I want to go to Tokyo from August 1-10',
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(true);
      expect(result.data?.metadata?.trip_plan_intent?.trip_info?.destination_city).toBe('Tokyo');
    });

    test('does not detect trip plan intent for general queries', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "The weather in Paris is usually pleasant in July.",
          metadata: {
            should_create_trip_plan: false
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        "What's the weather like in Paris?",
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(false);
    });

    test('creates trip plan structure when intent is detected', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I've created your trip plan!",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_created: true,
            trip_plan: {
              id: 'trip-123',
              name: 'Trip to Rome',
              destination: 'Rome',
              departure_date: '2024-09-15',
              return_date: '2024-09-22',
              travelers: 2,
              status: 'planning',
              saved_items: []
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'Create my trip plan to Rome for September 15-22',
        'session-123'
      );

      expect(result.data?.metadata?.trip_plan_created).toBe(true);
      expect(result.data?.metadata?.trip_plan?.name).toBe('Trip to Rome');
      expect(result.data?.metadata?.trip_plan?.destination).toBe('Rome');
    });
  });

  describe('Trip Plan Intent Phrases', () => {
    const intentPhrases = [
      { phrase: 'create a trip plan', expectedConfidence: 0.95 },
      { phrase: 'make my trip plan', expectedConfidence: 0.95 },
      { phrase: 'build my itinerary', expectedConfidence: 0.95 },
      { phrase: 'start planning my trip', expectedConfidence: 0.95 },
      { phrase: 'help me plan', expectedConfidence: 0.95 },
      { phrase: 'organize my trip', expectedConfidence: 0.95 },
      { phrase: 'save my trip', expectedConfidence: 0.95 },
      { phrase: 'add to my trip plan', expectedConfidence: 0.95 }
    ];

    test.each(intentPhrases)('detects intent for "$phrase"', async ({ phrase, expectedConfidence }) => {
      const mockResponse = {
        success: true,
        data: {
          message: `I'll help you ${phrase}!`,
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: expectedConfidence,
              reason: `User explicitly asked to '${phrase}'`
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        `I want to ${phrase} for my vacation`,
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(true);
      expect(result.data?.metadata?.trip_plan_intent?.confidence).toBe(expectedConfidence);
    });
  });

  describe('Context-based Trip Plan Detection', () => {
    test('detects intent when adding items after search results', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I'll add these to your trip plan!",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.85,
              reason: "User wants to add search results to trip plan"
            }
          },
          context: {
            has_search_results: true
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'Add this flight to my trip',
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(true);
    });

    test('maintains context in ongoing trip planning conversation', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I've updated your trip plan with the hotel information.",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.7,
              reason: "User is providing trip details in planning context"
            }
          },
          context: {
            trip_type: 'trip_planning'
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        "I'll need a hotel near the city center",
        'session-123'
      );

      expect(result.data?.metadata?.should_create_trip_plan).toBe(true);
    });
  });

  describe('Trip Plan Information Extraction', () => {
    test('extracts complete trip information', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "Creating your London trip plan!",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.95,
              trip_info: {
                destination_city: 'London',
                start_date: '2024-10-01',
                end_date: '2024-10-07',
                travelers: {
                  adults: 2,
                  children: 1,
                  infants: 0
                },
                preferences: ['direct flights', 'family-friendly']
              }
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'Create a trip plan to London Oct 1-7 for 2 adults and 1 child, prefer direct flights and family-friendly activities',
        'session-123'
      );

      const tripInfo = result.data?.metadata?.trip_plan_intent?.trip_info;
      expect(tripInfo?.destination_city).toBe('London');
      expect(tripInfo?.travelers?.adults).toBe(2);
      expect(tripInfo?.travelers?.children).toBe(1);
      expect(tripInfo?.preferences).toContain('direct flights');
      expect(tripInfo?.preferences).toContain('family-friendly');
    });

    test('handles partial trip information', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: "I'll help create your trip plan!",
          metadata: {
            should_create_trip_plan: true,
            trip_plan_intent: {
              wants_trip_plan: true,
              confidence: 0.9,
              trip_info: {
                destination_city: 'Barcelona'
                // Missing dates and travelers
              }
            }
          }
        }
      };

      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await unifiedTravelApi.sendChatMessage(
        'Plan my trip to Barcelona',
        'session-123'
      );

      const tripInfo = result.data?.metadata?.trip_plan_intent?.trip_info;
      expect(tripInfo?.destination_city).toBe('Barcelona');
      expect(tripInfo?.start_date).toBeUndefined();
      expect(tripInfo?.travelers).toBeUndefined();
    });
  });
});