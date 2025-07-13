import { TravelConversationalSearch } from './ConversationalSearch';
import { SearchQuery, SearchContext, SearchResult, UserPreferences } from '../types/AIAgentTypes';

describe('TravelConversationalSearch', () => {
  let conversationalSearch: TravelConversationalSearch;

  beforeEach(() => {
    conversationalSearch = new TravelConversationalSearch();
  });

  describe('refineSearch', () => {
    it('should refine search for cheaper options', () => {
      const initialQuery: SearchQuery = {
        query: 'flights to Tokyo',
        filters: { maxPrice: 1000 },
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(initialQuery, 'something cheaper');

      expect(refinedQuery.filters.maxPrice).toBe(800); // 80% of 1000
    });

    it('should refine search for more expensive options', () => {
      const initialQuery: SearchQuery = {
        query: 'hotels in Paris',
        filters: { minPrice: 100 },
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(initialQuery, 'more expensive luxury option');

      expect(refinedQuery.filters.minPrice).toBe(150); // 150% of 100
      expect(refinedQuery.filters.class).toBe('business');
    });

    it('should refine search for earlier times', () => {
      const initialQuery: SearchQuery = {
        query: 'flights to London',
        filters: { departureTime: '14:00' },
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(initialQuery, 'earlier flight');

      expect(refinedQuery.filters.departureTime).toBe('10:00'); // 4 hours earlier
    });

    it('should refine search for direct flights', () => {
      const initialQuery: SearchQuery = {
        query: 'flights to Tokyo',
        filters: {},
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(initialQuery, 'direct flights only');

      expect(refinedQuery.filters.maxStops).toBe(0);
      expect(refinedQuery.filters.maxDuration).toBe(480);
    });

    it('should add amenity filters', () => {
      const initialQuery: SearchQuery = {
        query: 'hotels in NYC',
        filters: {},
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(
        initialQuery, 
        'with wifi and parking'
      );

      expect(refinedQuery.filters.amenities).toContain('wifi');
      expect(refinedQuery.filters.amenities).toContain('parking');
    });

    it('should handle location preferences', () => {
      const initialQuery: SearchQuery = {
        query: 'hotels in Miami',
        filters: {},
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(
        initialQuery,
        'closer to downtown'
      );

      expect(refinedQuery.filters.nearLocation).toBe('downtown');
    });

    it('should adjust rating filters', () => {
      const initialQuery: SearchQuery = {
        query: 'hotels in LA',
        filters: { minRating: 3 },
        page: 1
      };

      const refinedQuery = conversationalSearch.refineSearch(
        initialQuery,
        'better rated hotels'
      );

      expect(refinedQuery.filters.minRating).toBe(4);
    });
  });

  describe('parseRelativeQuery', () => {
    it('should parse cheaper relative queries', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: { maxPrice: 500 },
        userFeedback: []
      };

      const query = conversationalSearch.parseRelativeQuery('something cheaper', context);

      expect(query.filters.maxPrice).toBe(350); // 70% of 500
    });

    it('should parse time-based relative queries', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const morningQuery = conversationalSearch.parseRelativeQuery('earlier flight', context);
      expect(morningQuery.filters.departureTimeRange).toBe('morning');

      const eveningQuery = conversationalSearch.parseRelativeQuery('later flight', context);
      expect(eveningQuery.filters.departureTimeRange).toBe('evening');

      const redEyeQuery = conversationalSearch.parseRelativeQuery('red-eye flight', context);
      expect(redEyeQuery.filters.departureTimeRange).toBe('night');
    });

    it('should parse location preferences', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const downtownQuery = conversationalSearch.parseRelativeQuery('closer to downtown', context);
      expect(downtownQuery.filters.locationPreference).toBe('downtown');

      const airportQuery = conversationalSearch.parseRelativeQuery('near the airport', context);
      expect(airportQuery.filters.locationPreference).toBe('airport');

      const beachQuery = conversationalSearch.parseRelativeQuery('by the beach', context);
      expect(beachQuery.filters.locationPreference).toBe('beach');
    });

    it('should handle sorting preferences', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const priceQuery = conversationalSearch.parseRelativeQuery('cheapest first', context);
      expect(priceQuery.sort).toBe('price_asc');

      const ratingQuery = conversationalSearch.parseRelativeQuery('best rated', context);
      expect(ratingQuery.sort).toBe('rating_desc');

      const popularQuery = conversationalSearch.parseRelativeQuery('most popular', context);
      expect(popularQuery.sort).toBe('popularity_desc');
    });

    it('should handle exclusions', () => {
      const context: SearchContext = {
        previousResults: [],
        appliedFilters: {},
        userFeedback: []
      };

      const excludeQuery = conversationalSearch.parseRelativeQuery(
        'flights except United',
        context
      );
      expect(excludeQuery.filters.exclude).toBe('United');

      const butNotQuery = conversationalSearch.parseRelativeQuery(
        'hotels but not downtown',
        context
      );
      expect(butNotQuery.filters.exclude).toBe('downtown');
    });
  });

  describe('formatResults', () => {
    it('should handle empty results', () => {
      const results: SearchResult[] = [];
      const preferences: UserPreferences = {};

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain("I couldn't find any options");
      expect(formatted).toContain("adjust the search parameters");
    });

    it('should format flight results', () => {
      const results: SearchResult[] = [
        {
          id: 'flight1',
          type: 'flight',
          data: {
            airline: 'United',
            departure: 'JFK',
            arrival: 'LAX',
            duration: '6h 30m',
            price: { amount: 350, currency: 'USD', displayPrice: '$350' },
            stops: 0
          },
          relevanceScore: 0.9
        }
      ];
      const preferences: UserPreferences = {
        travelStyle: 'comfort'
      };

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain('✈️ **Flights:**');
      expect(formatted).toContain('United');
      expect(formatted).toContain('$350');
      expect(formatted).toContain('Non-stop');
      expect(formatted).toContain('Direct flight for your comfort');
    });

    it('should format hotel results', () => {
      const results: SearchResult[] = [
        {
          id: 'hotel1',
          type: 'hotel',
          data: {
            name: 'Grand Hotel',
            rating: 4,
            price: { amount: 200, currency: 'USD', displayPrice: '$200' },
            location: 'Downtown NYC',
            amenities: ['wifi', 'pool', 'gym'],
            reviewScore: 8.5,
            reviewCount: 1250
          },
          relevanceScore: 0.8
        }
      ];
      const preferences: UserPreferences = {};

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain('🏨 **Hotels:**');
      expect(formatted).toContain('Grand Hotel');
      expect(formatted).toContain('$200/night');
      expect(formatted).toContain('⭐⭐⭐⭐');
      expect(formatted).toContain('Downtown NYC');
      expect(formatted).toContain('8.5/10 from 1250 reviews');
    });

    it('should format activity results', () => {
      const results: SearchResult[] = [
        {
          id: 'activity1',
          type: 'activity',
          data: {
            name: 'City Walking Tour',
            type: 'tour',
            price: { amount: 50, currency: 'USD', displayPrice: '$50' },
            location: 'Central Park',
            duration: '3 hours',
            rating: 4.5
          },
          relevanceScore: 0.7
        }
      ];
      const preferences: UserPreferences = {
        activityTypes: ['tour']
      };

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain('🎯 **Activities:**');
      expect(formatted).toContain('City Walking Tour');
      expect(formatted).toContain('$50');
      expect(formatted).toContain('Central Park');
      expect(formatted).toContain('3 hours');
      expect(formatted).toContain('4.5/5');
      expect(formatted).toContain('Matches your interests');
    });

    it('should add personalized recommendations', () => {
      const results: SearchResult[] = [
        {
          id: 'budget1',
          type: 'hotel',
          data: {
            name: 'Budget Inn',
            price: { amount: 80, currency: 'USD' }
          },
          relevanceScore: 0.6
        }
      ];
      const preferences: UserPreferences = {
        travelStyle: 'budget',
        budgetRange: [100, 300]
      };

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain('💡 **Recommendations based on your preferences:**');
      expect(formatted).toContain('budget-friendly options');
    });

    it('should highlight preferred airlines', () => {
      const results: SearchResult[] = [
        {
          id: 'flight1',
          type: 'flight',
          data: {
            airline: 'Delta',
            departure: 'JFK',
            arrival: 'LAX',
            duration: '6h',
            price: { amount: 400, currency: 'USD', displayPrice: '$400' },
            stops: 1
          },
          relevanceScore: 0.8
        }
      ];
      const preferences: UserPreferences = {
        preferredAirlines: ['Delta']
      };

      const formatted = conversationalSearch.formatResults(results, preferences);

      expect(formatted).toContain('⭐ Your preferred airline');
    });

    it('should limit results to 3 per type', () => {
      const results: SearchResult[] = Array.from({ length: 5 }, (_, i) => ({
        id: `flight${i}`,
        type: 'flight' as const,
        data: {
          airline: `Airline ${i}`,
          departure: 'JFK',
          arrival: 'LAX',
          duration: '6h',
          price: { amount: 300 + i * 50, currency: 'USD', displayPrice: `$${300 + i * 50}` },
          stops: 0
        },
        relevanceScore: 0.9 - i * 0.1
      }));
      const preferences: UserPreferences = {};

      const formatted = conversationalSearch.formatResults(results, preferences);

      // Should only show first 3 results
      expect(formatted).toContain('Airline 0');
      expect(formatted).toContain('Airline 1');
      expect(formatted).toContain('Airline 2');
      expect(formatted).not.toContain('Airline 3');
      expect(formatted).not.toContain('Airline 4');
    });
  });
});