import { useState, useCallback, useEffect } from 'react';
import {
  ConversationState,
  ConversationContext,
  EnhancedChatMessage,
  QuickAction,
  Intent,
  Entity
} from '../types/AIAgentTypes';
import { TravelNLUEngine } from '../services/NLUEngine';

interface ConversationStateHook {
  conversationState: ConversationState;
  context: ConversationContext;
  messages: EnhancedChatMessage[];
  quickActions: QuickAction[];
  addMessage: (message: Omit<EnhancedChatMessage, 'id' | 'timestamp'>) => void;
  updateContext: (updates: Partial<ConversationContext>) => void;
  transitionTo: (newState: ConversationState) => void;
  clearConversation: () => void;
  getContextualActions: () => QuickAction[];
}

export const useConversationState = (sessionId: string): ConversationStateHook => {
  const [conversationState, setConversationState] = useState<ConversationState>(
    ConversationState.GREETING
  );
  const [context, setContext] = useState<ConversationContext>({
    state: ConversationState.GREETING,
    entities: [],
    missingFields: [],
    lastIntent: null,
    clarificationNeeded: false
  });
  const [messages, setMessages] = useState<EnhancedChatMessage[]>([]);
  const [nluEngine] = useState(() => new TravelNLUEngine());

  // Load conversation state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem(`conversation-${sessionId}`);
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setConversationState(parsed.state || ConversationState.GREETING);
        setContext(parsed.context || context);
        setMessages(parsed.messages || []);
      } catch (error) {
        console.error('Failed to load conversation state:', error);
      }
    }
  }, [sessionId]);

  // Save conversation state to localStorage when it changes
  useEffect(() => {
    const stateToSave = {
      state: conversationState,
      context,
      messages: messages.slice(-50) // Keep last 50 messages
    };
    localStorage.setItem(`conversation-${sessionId}`, JSON.stringify(stateToSave));
  }, [conversationState, context, messages, sessionId]);

  const addMessage = useCallback((message: Omit<EnhancedChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: EnhancedChatMessage = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      metadata: message.metadata || {}
    };

    // Process user messages with NLU
    if (message.role === 'user') {
      const intent = nluEngine.extractIntent(message.content);
      const entities = nluEngine.extractEntities(message.content);
      
      newMessage.metadata.intent = intent;
      newMessage.metadata.entities = entities;

      // Update context based on new message
      setContext(prevContext => {
        const updatedMessages = [...messages, newMessage];
        const newContext = nluEngine.maintainContext(updatedMessages);
        
        // Determine next conversation state
        const nextState = determineNextState(intent, newContext, conversationState);
        setConversationState(nextState);
        
        return {
          ...newContext,
          state: nextState
        };
      });
    }

    setMessages(prev => [...prev, newMessage]);
  }, [messages, nluEngine, conversationState]);

  const updateContext = useCallback((updates: Partial<ConversationContext>) => {
    setContext(prev => ({ ...prev, ...updates }));
  }, []);

  const transitionTo = useCallback((newState: ConversationState) => {
    setConversationState(newState);
    setContext(prev => ({ ...prev, state: newState }));
  }, []);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationState(ConversationState.GREETING);
    setContext({
      state: ConversationState.GREETING,
      entities: [],
      missingFields: [],
      lastIntent: null,
      clarificationNeeded: false
    });
    localStorage.removeItem(`conversation-${sessionId}`);
  }, [sessionId]);

  const getContextualActions = useCallback((): QuickAction[] => {
    const quickActionsMap: Record<ConversationState, QuickAction[]> = {
      [ConversationState.GREETING]: [
        { label: "Plan a trip", icon: "✈️", action: "start_planning" },
        { label: "View my plans", icon: "📋", action: "view_plans" },
        { label: "Check bookings", icon: "🎫", action: "view_bookings" }
      ],
      [ConversationState.GATHERING_REQUIREMENTS]: [
        { label: "Popular destinations", icon: "🌍", action: "show_destinations" },
        { label: "Budget calculator", icon: "💰", action: "budget_tool" },
        { label: "Travel dates", icon: "📅", action: "date_picker" }
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
        { label: "New search", icon: "🆕", action: "new_search" }
      ],
      [ConversationState.ADDING_TO_PLAN]: [
        { label: "View plan", icon: "👁️", action: "view_current_plan" },
        { label: "Budget status", icon: "📊", action: "check_budget" },
        { label: "Continue searching", icon: "🔍", action: "continue_search" }
      ],
      [ConversationState.REVIEWING_PLAN]: [
        { label: "Book all", icon: "✅", action: "book_all" },
        { label: "Share plan", icon: "📤", action: "share_plan" },
        { label: "Export PDF", icon: "📄", action: "export_pdf" }
      ],
      [ConversationState.BOOKING]: [
        { label: "Payment info", icon: "💳", action: "payment_details" },
        { label: "Traveler details", icon: "👥", action: "traveler_info" },
        { label: "Review booking", icon: "📋", action: "review_booking" }
      ],
      [ConversationState.POST_BOOKING]: [
        { label: "View tickets", icon: "🎫", action: "view_tickets" },
        { label: "Add to calendar", icon: "📅", action: "add_calendar" },
        { label: "Plan another trip", icon: "✈️", action: "new_trip" }
      ]
    };

    return quickActionsMap[conversationState] || [];
  }, [conversationState]);

  const quickActions = getContextualActions();

  return {
    conversationState,
    context,
    messages,
    quickActions,
    addMessage,
    updateContext,
    transitionTo,
    clearConversation,
    getContextualActions
  };
};

// Helper function to determine next conversation state based on intent and context
function determineNextState(
  intent: Intent,
  context: ConversationContext,
  currentState: ConversationState
): ConversationState {
  // State transition logic based on intent and current state
  switch (intent.type) {
    case 'search_flight':
    case 'search_hotel':
      if (context.missingFields.length > 0) {
        return ConversationState.GATHERING_REQUIREMENTS;
      }
      return ConversationState.SEARCHING;

    case 'add_to_plan':
      return ConversationState.ADDING_TO_PLAN;

    case 'view_plan':
      return ConversationState.REVIEWING_PLAN;

    case 'book_item':
      return ConversationState.BOOKING;

    case 'get_recommendations':
      return ConversationState.SEARCHING;

    case 'check_budget':
      return ConversationState.REVIEWING_PLAN;

    case 'modify_plan':
      return ConversationState.REFINING_SEARCH;

    default:
      // State progression logic for unclear intents
      switch (currentState) {
        case ConversationState.GREETING:
          return ConversationState.GATHERING_REQUIREMENTS;
        
        case ConversationState.GATHERING_REQUIREMENTS:
          return context.missingFields.length > 0 
            ? ConversationState.GATHERING_REQUIREMENTS 
            : ConversationState.SEARCHING;
        
        case ConversationState.SEARCHING:
          return ConversationState.PRESENTING_OPTIONS;
        
        case ConversationState.PRESENTING_OPTIONS:
          return ConversationState.REFINING_SEARCH;
        
        default:
          return currentState;
      }
  }
}