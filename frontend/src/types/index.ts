// Main types exports
export * from './User';
export * from './TravelRequestTypes';
export * from './AIAgentTypes';

// Re-export commonly used types
export type { User, AuthState, LoginCredentials, RegisterData, UserPreferences } from './User';
export type { 
  TravelRequest, 
  FlightOption, 
  HotelOption, 
  ActivityOption, 
  Airport, 
  Location,
  Price,
  TravelSession 
} from './TravelRequestTypes';
export type {
  TravelAgent,
  ConversationState,
  EnhancedChatMessage,
  Intent,
  Entity,
  NLUEngine,
  PlanningAssistant,
  ConversationalSearch,
  AITravelService,
  CardResponse,
  QuickAction
} from './AIAgentTypes';