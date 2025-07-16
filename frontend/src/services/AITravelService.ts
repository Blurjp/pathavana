import {
  AITravelService,
  EnhancedChatMessage,
  AgentResponse,
  ConversationContext,
  Action,
  ActionResult,
  CardResponse,
  TextResponse,
  ConversationState
} from '../types/AIAgentTypes';
import { TravelNLUEngine } from './NLUEngine';
import { TravelConversationalSearch } from './ConversationalSearch';
import { apiClient } from './api';

export class TravelAIService implements AITravelService {
  private nluEngine: TravelNLUEngine;
  private conversationalSearch: TravelConversationalSearch;
  private sessionContexts: Map<string, ConversationContext>;

  constructor() {
    this.nluEngine = new TravelNLUEngine();
    this.conversationalSearch = new TravelConversationalSearch();
    this.sessionContexts = new Map();
  }

  async processMessage(
    message: EnhancedChatMessage,
    sessionId: string
  ): Promise<AgentResponse> {
    try {
      // Extract intent and entities from the message
      const intent = this.nluEngine.extractIntent(message.content);
      const entities = this.nluEngine.extractEntities(message.content);

      // Update message metadata
      message.metadata.intent = intent;
      message.metadata.entities = entities;

      // Get or create session context
      const context = this.sessionContexts.get(sessionId) || {
        state: ConversationState.GREETING,
        entities: [],
        missingFields: [],
        lastIntent: null,
        clarificationNeeded: false
      };

      // Send message to backend API
      const response = await apiClient.post(`/api/v1/travel/sessions/${sessionId}/chat`, {
        message: message.content,
        metadata: {
          intent: intent.type,
          entities: entities.map(e => ({
            type: e.type,
            value: e.value
          }))
        }
      });

      // Process the response based on type
      const agentResponse = this.processBackendResponse(response.data, context);

      // Update context
      context.lastIntent = intent;
      context.entities = [...context.entities, ...entities];
      this.sessionContexts.set(sessionId, context);

      return agentResponse;
    } catch (error) {
      console.error('Error processing message:', error);
      return {
        type: 'text',
        content: 'I apologize, but I encountered an error processing your request. Please try again.'
      } as TextResponse;
    }
  }

  async updateContext(
    sessionId: string,
    context: ConversationContext
  ): Promise<void> {
    this.sessionContexts.set(sessionId, context);
    
    // Sync context with backend
    try {
      await apiClient.put(`/api/v1/travel/sessions/${sessionId}/context`, {
        context: {
          state: context.state,
          entities: context.entities,
          missingFields: context.missingFields
        }
      });
    } catch (error) {
      console.error('Error updating context:', error);
    }
  }

  async executeAction(
    action: Action,
    context: ConversationContext
  ): Promise<ActionResult> {
    try {
      switch (action.type) {
        case 'add_to_plan':
          return await this.addToPlan(action.payload, context);
        
        case 'search':
          return await this.performSearch(action.payload, context);
        
        case 'book':
          return await this.bookItem(action.payload, context);
        
        case 'modify_plan':
          return await this.modifyPlan(action.payload, context);
        
        case 'get_recommendations':
          return await this.getRecommendations(action.payload, context);
        
        default:
          return {
            success: false,
            error: `Unknown action type: ${action.type}`
          };
      }
    } catch (error) {
      console.error('Error executing action:', error);
      return {
        success: false,
        error: 'Failed to execute action'
      };
    }
  }

  private processBackendResponse(
    response: any,
    context: ConversationContext
  ): AgentResponse {
    // Check if response contains search results
    if (response.searchResults) {
      return this.createCardResponse(response.searchResults, context);
    }

    // Check if response requires clarification
    if (response.clarificationNeeded) {
      return {
        type: 'text',
        content: response.clarificationQuestion || 'Could you provide more details?'
      } as TextResponse;
    }

    // Default text response
    return {
      type: 'text',
      content: response.response || response.message || 'I understand. How can I help you further?'
    } as TextResponse;
  }

  private createCardResponse(
    searchResults: any,
    context: ConversationContext
  ): CardResponse {
    const cards: any[] = [];

    // Process flight results
    if (searchResults.flights) {
      searchResults.flights.forEach((flight: any) => {
        cards.push({
          title: `${flight.airline} - ${flight.flightNumber}`,
          subtitle: `${flight.origin.city} → ${flight.destination.city}`,
          image: flight.airlineLogoUrl,
          details: {
            'Departure': this.formatDateTime(flight.departureTime),
            'Arrival': this.formatDateTime(flight.arrivalTime),
            'Duration': flight.duration,
            'Price': flight.price.displayPrice,
            'Stops': flight.stops === 0 ? 'Non-stop' : `${flight.stops} stop(s)`
          },
          actions: [
            {
              label: 'Add to Plan',
              action: 'add_to_plan',
              data: { type: 'flight', item: flight }
            },
            {
              label: 'View Details',
              action: 'view_details',
              data: { type: 'flight', id: flight.id }
            }
          ]
        });
      });
    }

    // Process hotel results
    if (searchResults.hotels) {
      searchResults.hotels.forEach((hotel: any) => {
        cards.push({
          title: hotel.name,
          subtitle: `${hotel.location.city} - ${hotel.rating}★`,
          image: hotel.images?.[0],
          details: {
            'Price': `${hotel.price.displayPrice}/night`,
            'Location': hotel.location.address,
            'Rating': `${hotel.reviewScore}/10 (${hotel.reviewCount} reviews)`,
            'Amenities': hotel.amenities.slice(0, 3).join(', ')
          },
          actions: [
            {
              label: 'Add to Plan',
              action: 'add_to_plan',
              data: { type: 'hotel', item: hotel }
            },
            {
              label: 'View Details',
              action: 'view_details',
              data: { type: 'hotel', id: hotel.id }
            }
          ]
        });
      });
    }

    // Process activity results
    if (searchResults.activities) {
      searchResults.activities.forEach((activity: any) => {
        cards.push({
          title: activity.name,
          subtitle: activity.type,
          image: activity.images?.[0],
          details: {
            'Price': activity.price.displayPrice,
            'Duration': activity.duration || 'Varies',
            'Location': activity.location.address,
            'Rating': activity.rating ? `${activity.rating}/5` : 'Not rated'
          },
          actions: [
            {
              label: 'Add to Plan',
              action: 'add_to_plan',
              data: { type: 'activity', item: activity }
            },
            {
              label: 'View Details',
              action: 'view_details',
              data: { type: 'activity', id: activity.id }
            }
          ]
        });
      });
    }

    return {
      type: 'card',
      cards
    };
  }

  private async addToPlan(payload: any, context: ConversationContext): Promise<ActionResult> {
    try {
      const response = await apiClient.post('/api/v1/travel/plan/items', payload);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to add item to plan'
      };
    }
  }

  private async performSearch(payload: any, context: ConversationContext): Promise<ActionResult> {
    try {
      const searchQuery = {
        query: payload.query,
        filters: payload.filters || {},
        sort: payload.sort,
        page: payload.page || 1
      };

      // Use conversational search if this is a refinement
      if (payload.isRefinement && payload.userFeedback) {
        const refinedQuery = this.conversationalSearch.refineSearch(
          searchQuery,
          payload.userFeedback
        );
        Object.assign(searchQuery, refinedQuery);
      }

      const response = await apiClient.post('/api/v1/travel/search', searchQuery);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to perform search'
      };
    }
  }

  private async bookItem(payload: any, context: ConversationContext): Promise<ActionResult> {
    try {
      const response = await apiClient.post('/api/v1/travel/bookings', payload);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to complete booking'
      };
    }
  }

  private async modifyPlan(payload: any, context: ConversationContext): Promise<ActionResult> {
    try {
      const response = await apiClient.put(`/api/v1/travel/plan/${payload.planId}`, payload.changes);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to modify plan'
      };
    }
  }

  private async getRecommendations(payload: any, context: ConversationContext): Promise<ActionResult> {
    try {
      const response = await apiClient.get('/api/v1/travel/recommendations', {
        params: {
          destination: payload.destination,
          type: payload.type,
          preferences: JSON.stringify(payload.preferences)
        }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to get recommendations'
      };
    }
  }

  private formatDateTime(dateTimeString: string): string {
    const date = new Date(dateTimeString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }

  // Stream support for real-time responses
  async streamMessage(
    message: string,
    sessionId: string,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const eventSource = new EventSource(
      `/api/v1/travel/sessions/${sessionId}/chat/stream?message=${encodeURIComponent(message)}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.chunk) {
        onChunk(data.chunk);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    // Clean up after stream completes
    return new Promise((resolve) => {
      eventSource.addEventListener('complete', () => {
        eventSource.close();
        resolve();
      });
    });
  }
}