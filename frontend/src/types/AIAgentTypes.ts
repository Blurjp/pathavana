// AI Travel Agent Types based on TRAVEL_AGENT_CHAT_SYSTEM.md

// Core AI Agent Capabilities
export interface TravelAgent {
  // Core abilities
  capabilities: {
    search: boolean;          // Search flights, hotels, activities
    plan: boolean;           // Create and manage travel plans
    book: boolean;           // Execute bookings
    modify: boolean;         // Change existing bookings
    recommend: boolean;      // Suggest destinations and activities
    budget: boolean;         // Track and optimize spending
  };
  
  // Context understanding
  context: {
    current_plan: TravelPlan | null;
    conversation_state: ConversationState;
    user_preferences: UserPreferences;
    search_history: SearchQuery[];
  };
}

// Conversation Flow States
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

// Enhanced Chat Message Structure
export interface EnhancedChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  metadata: {
    intent?: Intent;
    entities?: Entity[];
    actions?: Action[];
    attachments?: Attachment[];
  };
}

// Intent Recognition
export interface Intent {
  type: 'search_flight' | 'search_hotel' | 'add_to_plan' | 
        'view_plan' | 'modify_plan' | 'book_item' | 
        'get_recommendations' | 'check_budget';
  confidence: number;
  parameters: Record<string, any>;
}

// Entity Extraction
export interface Entity {
  type: 'destination' | 'date' | 'budget' | 'travelers' | 'preference';
  value: any;
  confidence: number;
  position: [number, number]; // Start and end position in text
}

// NLU Engine Interface
export interface NLUEngine {
  // Extract travel intent from user messages
  extractIntent(message: string): Intent;
  
  // Identify entities (dates, locations, preferences)
  extractEntities(message: string): Entity[];
  
  // Understand context from conversation history
  maintainContext(messages: EnhancedChatMessage[]): ConversationContext;
  
  // Handle ambiguous requests
  clarifyIntent(message: string, context: ConversationContext): ClarificationRequest;
}

// Planning Assistant Interface
export interface PlanningAssistant {
  // Create plan from conversation
  createPlanFromChat(messages: EnhancedChatMessage[]): TravelPlan;
  
  // Suggest next steps
  suggestNextActions(plan: TravelPlan): Suggestion[];
  
  // Detect and resolve conflicts
  analyzeConflicts(plan: TravelPlan): ConflictAnalysis;
  
  // Optimize itinerary
  optimizeItinerary(plan: TravelPlan): OptimizationResult;
}

// Suggestion Type
export interface Suggestion {
  type: 'add_flight' | 'book_hotel' | 'add_activity' | 'set_budget';
  priority: 'high' | 'medium' | 'low';
  message: string;
  action: () => void;
}

// Conversational Search Interface
export interface ConversationalSearch {
  // Multi-turn search refinement
  refineSearch(
    initialQuery: SearchQuery,
    userFeedback: string
  ): SearchQuery;
  
  // Understand relative queries
  parseRelativeQuery(
    query: string,
    context: SearchContext
  ): SearchQuery;
  
  // Present results conversationally
  formatResults(
    results: SearchResult[],
    preferences: UserPreferences
  ): string;
}

// Plan Manager Interface
export interface PlanManager {
  // Add items with natural language
  addItemFromDescription(
    description: string,
    plan: TravelPlan
  ): PlanItem;
  
  // Modify plan conversationally
  modifyPlan(
    instruction: string,
    plan: TravelPlan
  ): TravelPlan;
  
  // Summarize plan in natural language
  generatePlanSummary(plan: TravelPlan): string;
  
  // Track plan changes
  explainChanges(
    oldPlan: TravelPlan,
    newPlan: TravelPlan
  ): string;
}

// Message Types
export type UserMessage = 
  | TextMessage
  | VoiceMessage
  | ImageMessage
  | DocumentMessage;

// Agent Response Types
export type AgentResponse =
  | TextResponse
  | CardResponse
  | ListResponse
  | FormResponse
  | ConfirmationResponse;

// Rich Card Response
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

// Quick Actions
export interface QuickAction {
  label: string;
  icon: string;
  action: string;
  context?: any;
}

// Chat Visualization Interface
export interface ChatVisualization {
  // Timeline view of trip
  renderTimeline(plan: TravelPlan): TimelineComponent;
  
  // Budget breakdown
  renderBudget(budget: Budget): BudgetChart;
  
  // Map view of destinations
  renderMap(destinations: Destination[]): MapComponent;
  
  // Calendar for date selection
  renderCalendar(availability: DateAvailability): CalendarComponent;
}

// AI Service Architecture
export interface AITravelService {
  // Process chat messages
  processMessage(
    message: EnhancedChatMessage,
    sessionId: string
  ): Promise<AgentResponse>;
  
  // Maintain conversation context
  updateContext(
    sessionId: string,
    context: ConversationContext
  ): Promise<void>;
  
  // Execute actions
  executeAction(
    action: Action,
    context: ConversationContext
  ): Promise<ActionResult>;
}

// Travel API Adapter
export interface TravelAPIAdapter {
  // Search with natural language parameters
  searchFlights(params: NaturalSearchParams): Promise<Flight[]>;
  
  // Add to plan with validation
  addToPlan(
    item: any,
    planId: string
  ): Promise<PlanUpdateResult>;
  
  // Execute booking
  book(
    items: PlanItem[],
    paymentInfo: PaymentInfo
  ): Promise<BookingResult>;
}

// Conversation Store
export interface ConversationStore {
  // Session management
  sessions: Map<string, Session>;
  
  // Conversation history
  messages: Map<string, EnhancedChatMessage[]>;
  
  // Active plans
  activePlans: Map<string, TravelPlan>;
  
  // User preferences learned from chat
  learnedPreferences: Map<string, UserPreferences>;
}

// Supporting Types
export interface ConversationContext {
  state: ConversationState;
  entities: Entity[];
  missingFields: string[];
  lastIntent: Intent | null;
  clarificationNeeded: boolean;
}

export interface ClarificationRequest {
  question: string;
  options?: string[];
  type: 'single_choice' | 'multiple_choice' | 'open_ended';
}

export interface SearchQuery {
  query: string;
  filters: Record<string, any>;
  sort?: string;
  page?: number;
}

export interface SearchContext {
  previousResults: SearchResult[];
  appliedFilters: Record<string, any>;
  userFeedback: string[];
}

export interface SearchResult {
  id: string;
  type: 'flight' | 'hotel' | 'activity';
  data: any;
  relevanceScore: number;
}

export interface TravelPlan {
  id: string;
  name: string;
  destinations: Destination[];
  items: PlanItem[];
  budget: Budget;
  travelers: TravelerInfo[];
  status: 'draft' | 'confirmed' | 'booked';
}

export interface PlanItem {
  id: string;
  type: 'flight' | 'hotel' | 'activity';
  details: any;
  status: 'pending' | 'confirmed' | 'booked';
}

export interface ConflictAnalysis {
  conflicts: Conflict[];
  resolutionSuggestions: string[];
}

export interface Conflict {
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

export interface OptimizationResult {
  optimizedPlan: TravelPlan;
  savings: number;
  improvements: string[];
}

export interface NaturalSearchParams {
  naturalQuery: string;
  extractedEntities: Entity[];
  context: ConversationContext;
}

export interface PlanUpdateResult {
  success: boolean;
  updatedPlan: TravelPlan;
  message: string;
}

export interface BookingResult {
  success: boolean;
  bookingReferences: string[];
  totalCost: number;
}

export interface UserPreferences {
  preferredAirlines?: string[];
  hotelChains?: string[];
  activityTypes?: string[];
  budgetRange?: [number, number];
  travelStyle?: 'budget' | 'comfort' | 'luxury';
}

export interface TextMessage {
  type: 'text';
  content: string;
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
  fileName: string;
}

export interface TextResponse {
  type: 'text';
  content: string;
}

export interface ListResponse {
  type: 'list';
  items: any[];
}

export interface FormResponse {
  type: 'form';
  fields: FormField[];
}

export interface ConfirmationResponse {
  type: 'confirmation';
  message: string;
  actions: Array<{label: string; value: any}>;
}

export interface Action {
  type: string;
  payload: any;
}

export interface ActionResult {
  success: boolean;
  data?: any;
  error?: string;
}

export interface Attachment {
  type: string;
  url: string;
  metadata?: any;
}

export interface Session {
  id: string;
  userId?: string;
  startTime: Date;
  lastActivity: Date;
  context: ConversationContext;
}

export interface PaymentInfo {
  method: string;
  details: any;
}

export interface Destination {
  name: string;
  coordinates?: [number, number];
  country?: string;
}

export interface Budget {
  total: number;
  allocated: number;
  currency: string;
}

export interface TravelerInfo {
  name: string;
  age?: number;
  preferences?: any;
}

export interface FormField {
  name: string;
  type: string;
  label: string;
  required: boolean;
  options?: any[];
}

export interface TimelineComponent {
  render(): JSX.Element;
}

export interface BudgetChart {
  render(): JSX.Element;
}

export interface MapComponent {
  render(): JSX.Element;
}

export interface CalendarComponent {
  render(): JSX.Element;
}

export interface DateAvailability {
  availableDates: Date[];
  blockedDates: Date[];
}

export interface Flight {
  // Flight details matching existing FlightOption type
  id: string;
  [key: string]: any;
}