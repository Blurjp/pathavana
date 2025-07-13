// Core Travel Agent Types and Interfaces

export interface TravelAgent {
  capabilities: {
    search: boolean;
    plan: boolean;
    book: boolean;
    modify: boolean;
    recommend: boolean;
    budget: boolean;
  };
  
  context: {
    current_plan: TravelPlan | null;
    conversation_state: ConversationState;
    user_preferences: UserPreferences;
    search_history: SearchQuery[];
  };
}

export enum ConversationState {
  GREETING = 'greeting',
  GATHERING_REQUIREMENTS = 'gathering_requirements',
  SEARCHING = 'searching',
  PRESENTING_OPTIONS = 'presenting_options',
  REFINING_SEARCH = 'refining_search',
  ADDING_TO_PLAN = 'adding_to_plan',
  REVIEWING_PLAN = 'reviewing_plan',
  BOOKING = 'booking',
  POST_BOOKING = 'post_booking'
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    intent?: Intent;
    entities?: Entity[];
    actions?: Action[];
    attachments?: Attachment[];
  };
}

export interface Intent {
  type: 'search_flight' | 'search_hotel' | 'add_to_plan' | 
        'view_plan' | 'modify_plan' | 'book_item' | 
        'get_recommendations' | 'check_budget' | 'general_query';
  confidence: number;
  parameters: Record<string, any>;
}

export interface Entity {
  type: 'destination' | 'date' | 'budget' | 'travelers' | 'preference';
  value: any;
  confidence: number;
  position: [number, number];
}

export interface Action {
  type: string;
  label: string;
  data: any;
  callback?: () => void;
}

export interface Attachment {
  type: 'image' | 'document' | 'link';
  url: string;
  title?: string;
}

export interface TravelPlan {
  id: string;
  name: string;
  destination: string;
  startDate: Date;
  endDate: Date;
  travelers: number;
  budget: Budget;
  items: PlanItem[];
  status: 'draft' | 'confirmed' | 'booked';
  createdAt: Date;
  updatedAt: Date;
}

export interface Budget {
  total: number;
  allocated: number;
  currency: string;
  breakdown: {
    flights: number;
    hotels: number;
    activities: number;
    other: number;
  };
}

export interface PlanItem {
  id: string;
  type: 'flight' | 'hotel' | 'activity';
  status: 'searching' | 'selected' | 'booked';
  details: any;
  price: number;
  addedAt: Date;
}

export interface UserPreferences {
  preferredClass?: 'economy' | 'business' | 'first';
  hotelRating?: number;
  mealPreference?: string;
  activityTypes?: string[];
  budgetFlexibility?: 'strict' | 'flexible' | 'generous';
}

export interface SearchQuery {
  id: string;
  type: 'flight' | 'hotel' | 'activity';
  parameters: Record<string, any>;
  timestamp: Date;
  results?: any[];
}

// Message Types
export type UserMessage = 
  | TextMessage
  | VoiceMessage
  | ImageMessage
  | DocumentMessage;

export interface TextMessage {
  type: 'text';
  text: string;
}

export interface VoiceMessage {
  type: 'voice';
  audioUrl: string;
  transcript?: string;
}

export interface ImageMessage {
  type: 'image';
  imageUrl: string;
  caption?: string;
}

export interface DocumentMessage {
  type: 'document';
  documentUrl: string;
  filename: string;
}

// Agent Response Types
export type AgentResponse =
  | TextResponse
  | CardResponse
  | ListResponse
  | FormResponse
  | ConfirmationResponse;

export interface TextResponse {
  type: 'text';
  text: string;
  suggestions?: string[];
}

export interface CardResponse {
  type: 'card';
  cards: Array<{
    title: string;
    subtitle: string;
    image?: string;
    details: Record<string, string>;
    actions: Array<{
      label: string;
      action: 'add_to_plan' | 'book_now' | 'view_details';
      data: any;
    }>;
  }>;
}

export interface ListResponse {
  type: 'list';
  title: string;
  items: Array<{
    title: string;
    description: string;
    action?: Action;
  }>;
}

export interface FormResponse {
  type: 'form';
  title: string;
  fields: Array<{
    name: string;
    label: string;
    type: 'text' | 'date' | 'number' | 'select';
    options?: string[];
    required?: boolean;
  }>;
  submitAction: Action;
}

export interface ConfirmationResponse {
  type: 'confirmation';
  title: string;
  message: string;
  confirmAction: Action;
  cancelAction?: Action;
}

// Quick Actions
export interface QuickAction {
  label: string;
  icon: string;
  action: string;
  context?: any;
}

// NLU Types
export interface NLUResult {
  intent: Intent;
  entities: Entity[];
  confidence: number;
  suggestedResponse?: string;
}

export interface ConversationContext {
  sessionId: string;
  state: ConversationState;
  currentPlan?: TravelPlan;
  lastIntent?: Intent;
  entities: Map<string, Entity>;
  history: ChatMessage[];
}

// Planning Assistant Types
export interface Suggestion {
  type: 'add_flight' | 'book_hotel' | 'add_activity' | 'set_budget';
  priority: 'high' | 'medium' | 'low';
  message: string;
  action: () => void;
}

export interface ConflictAnalysis {
  hasConflicts: boolean;
  conflicts: Array<{
    type: 'timing' | 'budget' | 'availability';
    description: string;
    suggestion: string;
  }>;
}

export interface OptimizationResult {
  optimized: boolean;
  savings?: number;
  suggestions: string[];
  newItinerary?: PlanItem[];
}