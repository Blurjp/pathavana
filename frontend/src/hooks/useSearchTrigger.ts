import { useEffect, useCallback } from 'react';
import { ChatMessage } from '../types';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { useSidebar } from '../contexts/SidebarContext';

interface SearchIntent {
  type: 'flight' | 'hotel' | 'activity' | null;
  origin?: string;
  destination?: string;
  checkIn?: string;
  checkOut?: string;
  departureDate?: string;
  returnDate?: string;
  location?: string;
  travelers?: number;
}

interface UseSearchTriggerProps {
  sessionId?: string;
  onSearchTriggered?: (intent: SearchIntent) => void;
  onSearchComplete?: (results: any) => void;
  autoTrigger?: boolean;
}

// Keywords that indicate search intent
const FLIGHT_KEYWORDS = [
  'flight', 'flights', 'fly', 'flying', 'book flight', 'find flight',
  'plane', 'airplane', 'airfare', 'round trip', 'one way', 'direct flight',
  'connecting flight', 'nonstop', 'travel from', 'depart', 'departure'
];

const HOTEL_KEYWORDS = [
  'hotel', 'hotels', 'accommodation', 'stay', 'lodging', 'book hotel',
  'find hotel', 'place to stay', 'where to stay', 'check in', 'check out',
  'resort', 'motel', 'inn', 'bed and breakfast', 'nights'
];

const ACTIVITY_KEYWORDS = [
  'activity', 'activities', 'things to do', 'attractions', 'tours',
  'sightseeing', 'entertainment', 'experiences', 'visit', 'explore',
  'adventure', 'excursion', 'what to do', 'places to visit'
];

export const useSearchTrigger = ({
  sessionId,
  onSearchTriggered,
  onSearchComplete,
  autoTrigger = true
}: UseSearchTriggerProps) => {
  const { toggleSidebar, setActiveTab, setLoading, sidebarOpen } = useSidebar();

  const detectSearchIntent = useCallback((message: string): SearchIntent => {
    const lowerMessage = message.toLowerCase();
    
    // Check for flight intent
    const hasFlightKeyword = FLIGHT_KEYWORDS.some(keyword => 
      lowerMessage.includes(keyword)
    );
    
    // Check for hotel intent
    const hasHotelKeyword = HOTEL_KEYWORDS.some(keyword => 
      lowerMessage.includes(keyword)
    );
    
    // Check for activity intent
    const hasActivityKeyword = ACTIVITY_KEYWORDS.some(keyword => 
      lowerMessage.includes(keyword)
    );

    // Extract dates using simple regex patterns
    const datePattern = /\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b/g;
    const monthPattern = /\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b/i;
    
    // Extract locations (simple heuristic - words after "to", "from", "in", "at")
    const locationPattern = /(?:to|from|in|at)\s+([A-Z][a-zA-Z\s]+?)(?:\s+(?:on|from|to|in|at|for)|[,.]|$)/gi;
    const locations = [...message.matchAll(locationPattern)].map(match => match[1].trim());

    // Extract traveler count
    const travelerPattern = /(\d+)\s*(?:person|people|traveler|travelers|passenger|passengers|adult|adults)/i;
    const travelerMatch = message.match(travelerPattern);
    const travelers = travelerMatch ? parseInt(travelerMatch[1]) : undefined;

    // Determine primary intent based on keywords
    let type: 'flight' | 'hotel' | 'activity' | null = null;
    
    if (hasFlightKeyword) {
      type = 'flight';
    } else if (hasHotelKeyword) {
      type = 'hotel';
    } else if (hasActivityKeyword) {
      type = 'activity';
    }

    // Build intent object
    const intent: SearchIntent = {
      type,
      travelers
    };

    // Add location data based on intent type
    if (type === 'flight' && locations.length >= 2) {
      intent.origin = locations[0];
      intent.destination = locations[1];
    } else if (type === 'hotel' && locations.length > 0) {
      intent.location = locations[0];
    } else if (type === 'activity' && locations.length > 0) {
      intent.location = locations[0];
    }

    return intent;
  }, []);

  const triggerSearch = useCallback(async (message: string) => {
    if (!sessionId || !autoTrigger) return;

    const intent = detectSearchIntent(message);
    
    if (intent.type) {
      // Notify that search was triggered
      if (onSearchTriggered) {
        onSearchTriggered(intent);
      }

      // Open sidebar and set appropriate tab
      if (!sidebarOpen) {
        toggleSidebar();
      }
      
      setActiveTab(intent.type === 'activity' ? 'activities' : intent.type + 's' as any);
      setLoading(true);

      try {
        // The backend will handle the search based on the message content
        // We just need to ensure the UI is ready to display results
        
        // Add a small delay to allow the chat response to process
        setTimeout(() => {
          setLoading(false);
        }, 2000);
        
      } catch (error) {
        console.error('Error triggering search:', error);
        setLoading(false);
      }
    }
  }, [sessionId, autoTrigger, sidebarOpen, toggleSidebar, setActiveTab, setLoading, onSearchTriggered]);

  const processMessage = useCallback((message: ChatMessage) => {
    if (message.type === 'user' && autoTrigger) {
      triggerSearch(message.content);
    }
    
    // Check if assistant message contains search results
    if (message.type === 'assistant' && message.metadata?.searchResults) {
      if (!sidebarOpen) {
        toggleSidebar();
      }
      
      // Determine which tab to show based on results
      const results = message.metadata.searchResults;
      if (results.flights && results.flights.length > 0) {
        setActiveTab('flights');
      } else if (results.hotels && results.hotels.length > 0) {
        setActiveTab('hotels');
      } else if (results.activities && results.activities.length > 0) {
        setActiveTab('activities');
      }
      
      if (onSearchComplete) {
        onSearchComplete(results);
      }
    }
  }, [autoTrigger, sidebarOpen, toggleSidebar, setActiveTab, triggerSearch, onSearchComplete]);

  return {
    detectSearchIntent,
    triggerSearch,
    processMessage
  };
};