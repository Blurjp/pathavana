import { 
  ConversationState, 
  ConversationContext, 
  ChatMessage, 
  Intent,
  Entity,
  TravelPlan,
  QuickAction
} from '../types/travelAgent';

export class ConversationService {
  private contexts: Map<string, ConversationContext> = new Map();

  // Initialize a new conversation
  initializeConversation(sessionId: string): ConversationContext {
    const context: ConversationContext = {
      sessionId,
      state: ConversationState.GREETING,
      entities: new Map(),
      history: []
    };
    
    this.contexts.set(sessionId, context);
    return context;
  }

  // Get or create conversation context
  getContext(sessionId: string): ConversationContext {
    if (!this.contexts.has(sessionId)) {
      return this.initializeConversation(sessionId);
    }
    return this.contexts.get(sessionId)!;
  }

  // Update conversation state
  updateState(sessionId: string, newState: ConversationState): void {
    const context = this.getContext(sessionId);
    context.state = newState;
    this.contexts.set(sessionId, context);
  }

  // Add message to history
  addMessage(sessionId: string, message: ChatMessage): void {
    const context = this.getContext(sessionId);
    context.history.push(message);
    
    // Keep only last 50 messages for performance
    if (context.history.length > 50) {
      context.history = context.history.slice(-50);
    }
    
    this.contexts.set(sessionId, context);
  }

  // Update entities from message
  updateEntities(sessionId: string, entities: Entity[]): void {
    const context = this.getContext(sessionId);
    
    entities.forEach(entity => {
      // Update only if confidence is higher than existing
      const existing = context.entities.get(entity.type);
      if (!existing || entity.confidence > existing.confidence) {
        context.entities.set(entity.type, entity);
      }
    });
    
    this.contexts.set(sessionId, context);
  }

  // Set current plan
  setCurrentPlan(sessionId: string, plan: TravelPlan): void {
    const context = this.getContext(sessionId);
    context.currentPlan = plan;
    this.contexts.set(sessionId, context);
  }

  // Get quick actions based on current state
  getQuickActions(sessionId: string): QuickAction[] {
    const context = this.getContext(sessionId);
    
    const quickActionMap: Record<ConversationState, QuickAction[]> = {
      [ConversationState.GREETING]: [
        { label: "Plan a trip", icon: "✈️", action: "start_planning" },
        { label: "View my plans", icon: "📋", action: "view_plans" },
        { label: "Check bookings", icon: "🎫", action: "view_bookings" }
      ],
      [ConversationState.GATHERING_REQUIREMENTS]: [
        { label: "Popular destinations", icon: "🌟", action: "show_destinations" },
        { label: "Budget calculator", icon: "💰", action: "calculate_budget" },
        { label: "Travel dates", icon: "📅", action: "select_dates" }
      ],
      [ConversationState.SEARCHING]: [
        { label: "Change dates", icon: "📅", action: "modify_dates" },
        { label: "Filter results", icon: "🔍", action: "add_filters" },
        { label: "Compare options", icon: "⚖️", action: "compare" }
      ],
      [ConversationState.PRESENTING_OPTIONS]: [
        { label: "Sort by price", icon: "💲", action: "sort_price" },
        { label: "Sort by rating", icon: "⭐", action: "sort_rating" },
        { label: "Show more", icon: "➕", action: "load_more" }
      ],
      [ConversationState.REFINING_SEARCH]: [
        { label: "Reset filters", icon: "🔄", action: "reset_filters" },
        { label: "Save search", icon: "💾", action: "save_search" },
        { label: "Change destination", icon: "📍", action: "change_destination" }
      ],
      [ConversationState.ADDING_TO_PLAN]: [
        { label: "View plan", icon: "📋", action: "view_current_plan" },
        { label: "Compare selections", icon: "🔀", action: "compare_selections" },
        { label: "Calculate total", icon: "🧮", action: "calculate_total" }
      ],
      [ConversationState.REVIEWING_PLAN]: [
        { label: "Edit plan", icon: "✏️", action: "edit_plan" },
        { label: "Share plan", icon: "🔗", action: "share_plan" },
        { label: "Book now", icon: "✅", action: "proceed_booking" }
      ],
      [ConversationState.BOOKING]: [
        { label: "Payment options", icon: "💳", action: "show_payment" },
        { label: "Apply coupon", icon: "🎟️", action: "apply_coupon" },
        { label: "Review details", icon: "👁️", action: "review_booking" }
      ],
      [ConversationState.POST_BOOKING]: [
        { label: "View itinerary", icon: "📄", action: "view_itinerary" },
        { label: "Add to calendar", icon: "📅", action: "add_calendar" },
        { label: "Plan another trip", icon: "🆕", action: "new_trip" }
      ]
    };

    return quickActionMap[context.state] || [];
  }

  // Determine next state based on intent
  getNextState(currentState: ConversationState, intent: Intent): ConversationState {
    const stateTransitions: Record<ConversationState, Record<string, ConversationState>> = {
      [ConversationState.GREETING]: {
        'search_flight': ConversationState.GATHERING_REQUIREMENTS,
        'search_hotel': ConversationState.GATHERING_REQUIREMENTS,
        'view_plan': ConversationState.REVIEWING_PLAN,
        'get_recommendations': ConversationState.GATHERING_REQUIREMENTS
      },
      [ConversationState.GATHERING_REQUIREMENTS]: {
        'search_flight': ConversationState.SEARCHING,
        'search_hotel': ConversationState.SEARCHING,
        'view_plan': ConversationState.REVIEWING_PLAN
      },
      [ConversationState.SEARCHING]: {
        'add_to_plan': ConversationState.ADDING_TO_PLAN,
        'search_flight': ConversationState.REFINING_SEARCH,
        'search_hotel': ConversationState.REFINING_SEARCH
      },
      [ConversationState.PRESENTING_OPTIONS]: {
        'add_to_plan': ConversationState.ADDING_TO_PLAN,
        'search_flight': ConversationState.REFINING_SEARCH,
        'search_hotel': ConversationState.REFINING_SEARCH,
        'view_plan': ConversationState.REVIEWING_PLAN
      },
      [ConversationState.REFINING_SEARCH]: {
        'add_to_plan': ConversationState.ADDING_TO_PLAN,
        'view_plan': ConversationState.REVIEWING_PLAN
      },
      [ConversationState.ADDING_TO_PLAN]: {
        'view_plan': ConversationState.REVIEWING_PLAN,
        'search_flight': ConversationState.SEARCHING,
        'search_hotel': ConversationState.SEARCHING,
        'book_item': ConversationState.BOOKING
      },
      [ConversationState.REVIEWING_PLAN]: {
        'modify_plan': ConversationState.ADDING_TO_PLAN,
        'book_item': ConversationState.BOOKING,
        'search_flight': ConversationState.SEARCHING,
        'search_hotel': ConversationState.SEARCHING
      },
      [ConversationState.BOOKING]: {
        'view_plan': ConversationState.REVIEWING_PLAN,
        'modify_plan': ConversationState.REVIEWING_PLAN
      },
      [ConversationState.POST_BOOKING]: {
        'search_flight': ConversationState.GATHERING_REQUIREMENTS,
        'search_hotel': ConversationState.GATHERING_REQUIREMENTS,
        'view_plan': ConversationState.REVIEWING_PLAN
      }
    };

    const transitions = stateTransitions[currentState];
    if (transitions && transitions[intent.type]) {
      return transitions[intent.type];
    }
    
    return currentState;
  }

  // Get conversation summary
  getConversationSummary(sessionId: string): string {
    const context = this.getContext(sessionId);
    const entities = Array.from(context.entities.values());
    
    const destination = entities.find(e => e.type === 'destination')?.value;
    const dates = entities.find(e => e.type === 'date')?.value;
    const budget = entities.find(e => e.type === 'budget')?.value;
    const travelers = entities.find(e => e.type === 'travelers')?.value;
    
    let summary = "Current conversation: ";
    
    if (destination) summary += `Trip to ${destination}`;
    if (dates) summary += `, ${dates}`;
    if (travelers) summary += `, ${travelers} traveler(s)`;
    if (budget) summary += `, budget: $${budget}`;
    
    if (context.currentPlan) {
      summary += `. Active plan: ${context.currentPlan.name}`;
    }
    
    return summary || "New conversation started";
  }

  // Clear conversation context
  clearContext(sessionId: string): void {
    this.contexts.delete(sessionId);
  }

  // Get all active sessions
  getActiveSessions(): string[] {
    return Array.from(this.contexts.keys());
  }
}