import { apiClient } from './api';
import { 
  TravelRequest, 
  ChatResponse, 
  TravelSession, 
  SearchResults,
  ApiResponse,
  TravelContext,
  Trip,
  ItineraryItem
} from '../types';

export class UnifiedTravelApi {
  private baseUrl = '/api/v1/travel';

  // Chat-based travel planning
  async sendChatMessage(
    message: string, 
    sessionId?: string
  ): Promise<ApiResponse<ChatResponse>> {
    if (sessionId && sessionId.trim()) {
      // Send to existing session
      return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/chat`, {
        message,
        metadata: {
          timestamp: new Date().toISOString(),
          source: 'chat_input'
        }
      });
    } else {
      // Create new session with initial message
      return apiClient.post(`${this.baseUrl}/sessions`, {
        message,
        source: 'web'
      });
    }
  }

  // Session management
  async createSession(initialMessage?: string): Promise<ApiResponse<{ 
    sessionId: string;
    session_id: string;
    initial_response?: string;
    metadata?: any;
    trip_context?: any;
    status?: string;
  }>> {
    return apiClient.post(`${this.baseUrl}/sessions`, {
      message: initialMessage || 'Hello, I want to plan a trip',
      source: 'web'
    });
  }
  
  async createEmptySession(): Promise<ApiResponse<{ 
    session_id: string;
    status: string;
    created_at: string;
  }>> {
    return apiClient.post(`${this.baseUrl}/sessions/new`, {});
  }

  async getSession(sessionId: string): Promise<ApiResponse<TravelSession>> {
    const response = await apiClient.get(`${this.baseUrl}/sessions/${sessionId}`);
    
    // Transform backend response to frontend format
    if (response.success && response.data) {
      const sessionData = response.data as any;
      const transformedSession: TravelSession = {
        id: sessionData.session_id || sessionId,
        userId: sessionData.user_id,
        messages: sessionData.session_data?.conversation_history || [],
        context: {
          currentRequest: sessionData.session_data?.parsed_intent,
          searchHistory: sessionData.session_data?.search_history || [],
          selectedOptions: sessionData.session_data?.selected_options || {
            flights: [],
            hotels: [],
            activities: []
          },
          trip: sessionData.plan_data
        },
        createdAt: sessionData.created_at,
        updatedAt: sessionData.updated_at,
        status: sessionData.status || 'active'
      };
      
      return {
        ...response,
        data: transformedSession
      };
    }
    
    return {
      ...response,
      data: null as any
    };
  }

  async updateSession(
    sessionId: string, 
    updates: Partial<TravelSession>
  ): Promise<ApiResponse<TravelSession>> {
    // Transform frontend format to backend format
    const backendUpdates = {
      session_data: {
        chat_messages: updates.messages,
        parsed_intent: updates.context?.currentRequest,
        search_history: updates.context?.searchHistory,
        selected_options: updates.context?.selectedOptions
      },
      plan_data: updates.context?.trip,
      updated_at: new Date().toISOString()
    };
    
    return apiClient.put(`${this.baseUrl}/sessions/${sessionId}`, backendUpdates);
  }

  async deleteSession(sessionId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`${this.baseUrl}/sessions/${sessionId}`);
  }

  // Context management
  async getContext(sessionId: string): Promise<ApiResponse<TravelContext>> {
    const response = await apiClient.get(`${this.baseUrl}/sessions/${sessionId}`);
    
    if (response.success && response.data) {
      const sessionData = response.data as any;
      const context: TravelContext = {
        currentRequest: sessionData.session_data?.parsed_intent,
        searchHistory: sessionData.session_data?.search_history || [],
        selectedOptions: sessionData.session_data?.selected_options || {
          flights: [],
          hotels: [],
          activities: []
        },
        trip: sessionData.plan_data
      };
      
      return {
        ...response,
        data: context
      };
    }
    
    return {
      ...response,
      data: null as any
    };
  }

  async updateContext(
    sessionId: string, 
    context: TravelContext
  ): Promise<ApiResponse<TravelContext>> {
    const updates = {
      session_data: {
        parsed_intent: context.currentRequest,
        search_history: context.searchHistory,
        selected_options: context.selectedOptions
      },
      plan_data: context.trip
    };
    
    return apiClient.put(`${this.baseUrl}/sessions/${sessionId}`, updates);
  }

  // Search operations
  async searchFlights(
    sessionId: string,
    request?: TravelRequest
  ): Promise<ApiResponse<SearchResults>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/search`, {
      search_types: ['flights'],
      force_refresh: false,
      request_override: request
    });
  }

  async searchHotels(
    sessionId: string,
    request?: TravelRequest
  ): Promise<ApiResponse<SearchResults>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/search`, {
      search_types: ['hotels'],
      force_refresh: false,
      request_override: request
    });
  }

  async searchActivities(
    sessionId: string,
    destination?: string,
    dateRange?: { start: string; end: string }
  ): Promise<ApiResponse<SearchResults>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/search`, {
      search_types: ['activities'],
      force_refresh: false,
      request_override: destination ? { destination, ...dateRange } : undefined
    });
  }

  // Unified search
  async unifiedSearch(
    sessionId: string,
    searchTypes: string[] = ['flights', 'hotels', 'activities'],
    forceRefresh: boolean = false
  ): Promise<ApiResponse<SearchResults>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/search`, {
      search_types: searchTypes,
      force_refresh: forceRefresh
    });
  }

  // Save items to trip
  async saveItemToTrip(
    sessionId: string,
    item: ItineraryItem
  ): Promise<ApiResponse<any>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/items`, {
      item_type: item.type,
      item_data: item,
      assigned_day: 1, // TODO: Calculate based on itinerary
      notes: item.description
    });
  }

  // Remove item from trip
  async removeItemFromTrip(
    sessionId: string,
    itemId: string
  ): Promise<ApiResponse<void>> {
    return apiClient.delete(`${this.baseUrl}/sessions/${sessionId}/items/${itemId}`);
  }

  // Update session dates
  async updateDates(
    sessionId: string,
    dates: { departure?: string; return?: string }
  ): Promise<ApiResponse<any>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/dates`, dates);
  }

  // Update session location
  async updateLocation(
    sessionId: string,
    location: { destination?: string; origin?: string }
  ): Promise<ApiResponse<any>> {
    return apiClient.post(`${this.baseUrl}/sessions/${sessionId}/location`, location);
  }

  // Get user's travel sessions
  async getUserSessions(): Promise<ApiResponse<TravelSession[]>> {
    return apiClient.get(`${this.baseUrl}/sessions`);
  }

  // Export session data (GDPR compliance)
  async exportSessionData(sessionId: string): Promise<ApiResponse<any>> {
    return apiClient.get(`${this.baseUrl}/sessions/${sessionId}/export`);
  }

  // Get session recommendations
  async getRecommendations(sessionId: string): Promise<ApiResponse<string[]>> {
    const response = await apiClient.get(`${this.baseUrl}/sessions/${sessionId}`);
    
    if (response.success && response.data) {
      const suggestions = (response.data as any).session_data?.suggestions || [];
      return {
        ...response,
        data: suggestions
      };
    }
    
    return { success: false, data: [] };
  }
}

export const unifiedTravelApi = new UnifiedTravelApi();