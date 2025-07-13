import {
  ConversationalSearch,
  SearchQuery,
  SearchContext,
  SearchResult,
  UserPreferences
} from '../types/AIAgentTypes';

export class TravelConversationalSearch implements ConversationalSearch {
  refineSearch(initialQuery: SearchQuery, userFeedback: string): SearchQuery {
    const refinedQuery = { ...initialQuery };
    const feedbackLower = userFeedback.toLowerCase();

    // Price refinements
    if (feedbackLower.includes('cheaper') || feedbackLower.includes('less expensive')) {
      refinedQuery.filters = {
        ...refinedQuery.filters,
        maxPrice: (refinedQuery.filters.maxPrice || 1000) * 0.8
      };
    } else if (feedbackLower.includes('more expensive') || feedbackLower.includes('luxury')) {
      refinedQuery.filters = {
        ...refinedQuery.filters,
        minPrice: (refinedQuery.filters.minPrice || 0) * 1.5,
        class: 'business'
      };
    }

    // Time refinements
    if (feedbackLower.includes('earlier')) {
      const currentTime = refinedQuery.filters.departureTime || '12:00';
      refinedQuery.filters = {
        ...refinedQuery.filters,
        departureTime: this.adjustTime(currentTime, -4)
      };
    } else if (feedbackLower.includes('later')) {
      const currentTime = refinedQuery.filters.departureTime || '12:00';
      refinedQuery.filters = {
        ...refinedQuery.filters,
        departureTime: this.adjustTime(currentTime, 4)
      };
    }

    // Duration refinements
    if (feedbackLower.includes('shorter') || feedbackLower.includes('direct')) {
      refinedQuery.filters = {
        ...refinedQuery.filters,
        maxStops: 0,
        maxDuration: refinedQuery.filters.maxDuration ? refinedQuery.filters.maxDuration * 0.8 : 480
      };
    }

    // Location refinements
    if (feedbackLower.includes('closer to') || feedbackLower.includes('near')) {
      const locationMatch = userFeedback.match(/(?:closer to|near)\s+(.+?)(?:\s|$)/i);
      if (locationMatch) {
        refinedQuery.filters = {
          ...refinedQuery.filters,
          nearLocation: locationMatch[1].trim()
        };
      }
    }

    // Amenity refinements
    const amenityKeywords = {
      'wifi': ['wifi', 'internet', 'wi-fi'],
      'parking': ['parking', 'car', 'vehicle'],
      'pool': ['pool', 'swimming'],
      'gym': ['gym', 'fitness', 'workout'],
      'breakfast': ['breakfast', 'morning meal'],
      'pet-friendly': ['pet', 'dog', 'cat']
    };

    Object.entries(amenityKeywords).forEach(([amenity, keywords]) => {
      if (keywords.some(keyword => feedbackLower.includes(keyword))) {
        refinedQuery.filters = {
          ...refinedQuery.filters,
          amenities: [...(refinedQuery.filters.amenities || []), amenity]
        };
      }
    });

    // Rating refinements
    if (feedbackLower.includes('better rated') || feedbackLower.includes('higher rating')) {
      refinedQuery.filters = {
        ...refinedQuery.filters,
        minRating: Math.min((refinedQuery.filters.minRating || 3) + 1, 5)
      };
    }

    // Airline/Hotel chain preferences
    const brandMatch = userFeedback.match(/(?:only|prefer)\s+(\w+)(?:\s+flights?|hotels?)?/i);
    if (brandMatch) {
      refinedQuery.filters = {
        ...refinedQuery.filters,
        preferredBrand: brandMatch[1]
      };
    }

    return refinedQuery;
  }

  parseRelativeQuery(query: string, context: SearchContext): SearchQuery {
    const queryLower = query.toLowerCase();
    const lastQuery = context.previousResults[0]?.data?.query || {};

    // Start with the base query from context
    const parsedQuery: SearchQuery = {
      query: query,
      filters: { ...lastQuery.filters },
      sort: lastQuery.sort,
      page: 1
    };

    // Handle relative price queries
    if (queryLower.includes('something cheaper')) {
      const currentMaxPrice = context.appliedFilters.maxPrice || 1000;
      parsedQuery.filters.maxPrice = currentMaxPrice * 0.7;
    } else if (queryLower.includes('something more expensive')) {
      const currentMinPrice = context.appliedFilters.minPrice || 0;
      parsedQuery.filters.minPrice = currentMinPrice * 1.3;
    }

    // Handle relative time queries
    if (queryLower.includes('earlier flight')) {
      parsedQuery.filters.departureTimeRange = 'morning';
    } else if (queryLower.includes('later flight')) {
      parsedQuery.filters.departureTimeRange = 'evening';
    } else if (queryLower.includes('red-eye')) {
      parsedQuery.filters.departureTimeRange = 'night';
    }

    // Handle relative location queries
    if (queryLower.includes('closer to downtown')) {
      parsedQuery.filters.locationPreference = 'downtown';
    } else if (queryLower.includes('near the airport')) {
      parsedQuery.filters.locationPreference = 'airport';
    } else if (queryLower.includes('by the beach')) {
      parsedQuery.filters.locationPreference = 'beach';
    }

    // Handle comparison queries
    if (queryLower.includes('like the') && queryLower.includes('but')) {
      // Extract the reference and modification
      const match = query.match(/like the (.+?) but (.+)/i);
      if (match) {
        const reference = match[1];
        const modification = match[2];
        
        // Find the referenced item in previous results
        const referencedItem = this.findReferencedItem(reference, context.previousResults);
        if (referencedItem) {
          parsedQuery.filters = { ...referencedItem.data.filters };
          // Apply the modification
          parsedQuery.query = `${referencedItem.data.baseQuery} ${modification}`;
        }
      }
    }

    // Handle sorting preferences
    if (queryLower.includes('cheapest first')) {
      parsedQuery.sort = 'price_asc';
    } else if (queryLower.includes('best rated')) {
      parsedQuery.sort = 'rating_desc';
    } else if (queryLower.includes('most popular')) {
      parsedQuery.sort = 'popularity_desc';
    }

    // Handle exclusions
    if (queryLower.includes('except') || queryLower.includes('but not')) {
      const excludeMatch = query.match(/(?:except|but not)\s+(.+)/i);
      if (excludeMatch) {
        parsedQuery.filters.exclude = excludeMatch[1].trim();
      }
    }

    return parsedQuery;
  }

  formatResults(results: SearchResult[], preferences: UserPreferences): string {
    if (results.length === 0) {
      return "I couldn't find any options matching your criteria. Would you like me to adjust the search parameters?";
    }

    let response = `I found ${results.length} great option${results.length > 1 ? 's' : ''} for you:\n\n`;

    // Group results by type
    const groupedResults = this.groupResultsByType(results);

    // Format flights
    if (groupedResults.flight && groupedResults.flight.length > 0) {
      response += this.formatFlightResults(groupedResults.flight, preferences);
    }

    // Format hotels
    if (groupedResults.hotel && groupedResults.hotel.length > 0) {
      response += this.formatHotelResults(groupedResults.hotel, preferences);
    }

    // Format activities
    if (groupedResults.activity && groupedResults.activity.length > 0) {
      response += this.formatActivityResults(groupedResults.activity, preferences);
    }

    // Add personalized recommendations based on preferences
    response += this.addPersonalizedRecommendations(results, preferences);

    return response;
  }

  private adjustTime(currentTime: string, hoursToAdd: number): string {
    const [hours, minutes] = currentTime.split(':').map(Number);
    let newHours = (hours + hoursToAdd) % 24;
    if (newHours < 0) newHours += 24;
    return `${newHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  }

  private findReferencedItem(reference: string, previousResults: SearchResult[]): SearchResult | null {
    const refLower = reference.toLowerCase();
    
    // Try to find by position (first, second, last)
    if (refLower.includes('first')) return previousResults[0] || null;
    if (refLower.includes('second')) return previousResults[1] || null;
    if (refLower.includes('last')) return previousResults[previousResults.length - 1] || null;
    
    // Try to find by name
    return previousResults.find(result => 
      result.data.name?.toLowerCase().includes(refLower)
    ) || null;
  }

  private groupResultsByType(results: SearchResult[]): Record<string, SearchResult[]> {
    return results.reduce((acc, result) => {
      if (!acc[result.type]) acc[result.type] = [];
      acc[result.type].push(result);
      return acc;
    }, {} as Record<string, SearchResult[]>);
  }

  private formatFlightResults(flights: SearchResult[], preferences: UserPreferences): string {
    let response = "✈️ **Flights:**\n";
    
    flights.slice(0, 3).forEach((flight, index) => {
      const data = flight.data;
      const price = this.formatPrice(data.price, preferences);
      const duration = this.formatDuration(data.duration);
      const stops = data.stops === 0 ? 'Non-stop' : `${data.stops} stop${data.stops > 1 ? 's' : ''}`;
      
      response += `${index + 1}. ${data.airline} - ${price}\n`;
      response += `   ${data.departure} → ${data.arrival} (${duration}, ${stops})\n`;
      
      // Add preference-based highlights
      if (preferences.preferredAirlines?.includes(data.airline)) {
        response += `   ⭐ Your preferred airline\n`;
      }
      if (data.stops === 0 && preferences.travelStyle === 'comfort') {
        response += `   ✓ Direct flight for your comfort\n`;
      }
      
      response += '\n';
    });
    
    return response;
  }

  private formatHotelResults(hotels: SearchResult[], preferences: UserPreferences): string {
    let response = "🏨 **Hotels:**\n";
    
    hotels.slice(0, 3).forEach((hotel, index) => {
      const data = hotel.data;
      const price = this.formatPrice(data.price, preferences);
      const rating = '⭐'.repeat(Math.round(data.rating));
      
      response += `${index + 1}. ${data.name} - ${price}/night ${rating}\n`;
      response += `   📍 ${data.location}\n`;
      
      // Highlight amenities matching preferences
      const matchingAmenities = data.amenities.filter((amenity: string) => 
        preferences.hotelChains?.includes(amenity)
      );
      if (matchingAmenities.length > 0) {
        response += `   ✓ ${matchingAmenities.join(', ')}\n`;
      }
      
      if (data.reviewScore) {
        response += `   📊 ${data.reviewScore}/10 from ${data.reviewCount} reviews\n`;
      }
      
      response += '\n';
    });
    
    return response;
  }

  private formatActivityResults(activities: SearchResult[], preferences: UserPreferences): string {
    let response = "🎯 **Activities:**\n";
    
    activities.slice(0, 3).forEach((activity, index) => {
      const data = activity.data;
      const price = this.formatPrice(data.price, preferences);
      
      response += `${index + 1}. ${data.name} - ${price}\n`;
      response += `   📍 ${data.location}\n`;
      if (data.duration) {
        response += `   ⏱️ ${data.duration}\n`;
      }
      if (data.rating) {
        response += `   ⭐ ${data.rating}/5\n`;
      }
      
      // Check if activity type matches preferences
      if (preferences.activityTypes?.includes(data.type)) {
        response += `   ✓ Matches your interests\n`;
      }
      
      response += '\n';
    });
    
    return response;
  }

  private formatPrice(price: any, preferences: UserPreferences): string {
    if (!price) return 'Price not available';
    
    const amount = typeof price === 'object' ? price.amount : price;
    const currency = typeof price === 'object' ? price.currency : 'USD';
    
    // Format based on user's travel style
    if (preferences.travelStyle === 'budget' && amount < (preferences.budgetRange?.[0] || 100)) {
      return `💰 ${currency} ${amount}`;
    } else if (preferences.travelStyle === 'luxury') {
      return `${currency} ${amount}`;
    }
    
    return `${currency} ${amount}`;
  }

  private formatDuration(duration: string | number): string {
    if (typeof duration === 'number') {
      const hours = Math.floor(duration / 60);
      const minutes = duration % 60;
      return `${hours}h ${minutes}m`;
    }
    return duration;
  }

  private addPersonalizedRecommendations(results: SearchResult[], preferences: UserPreferences): string {
    let recommendations = '\n💡 **Recommendations based on your preferences:**\n';
    
    // Budget-based recommendations
    if (preferences.travelStyle === 'budget') {
      const budgetOptions = results.filter(r => 
        r.data.price && r.data.price.amount < (preferences.budgetRange?.[0] || 500)
      );
      if (budgetOptions.length > 0) {
        recommendations += '• I found some great budget-friendly options that match your style\n';
      }
    }
    
    // Comfort-based recommendations
    if (preferences.travelStyle === 'comfort' || preferences.travelStyle === 'luxury') {
      const comfortOptions = results.filter(r => 
        (r.type === 'flight' && r.data.stops === 0) ||
        (r.type === 'hotel' && r.data.rating >= 4)
      );
      if (comfortOptions.length > 0) {
        recommendations += '• Several options offer the comfort level you prefer\n';
      }
    }
    
    // Activity-based recommendations
    if (preferences.activityTypes && preferences.activityTypes.length > 0) {
      const matchingActivities = results.filter(r => 
        r.type === 'activity' && preferences.activityTypes?.includes(r.data.type)
      );
      if (matchingActivities.length > 0) {
        recommendations += `• Found activities matching your interests: ${preferences.activityTypes.join(', ')}\n`;
      }
    }
    
    recommendations += '\nWould you like me to refine these results or add any to your travel plan?';
    
    return recommendations;
  }
}