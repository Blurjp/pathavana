// Core travel request types
export interface TravelRequest {
  id?: string;
  sessionId?: string;
  query: string;
  origin?: string;
  destination?: string;
  departureDate?: string;
  returnDate?: string;
  travelers: number;
  travelClass?: 'economy' | 'premium_economy' | 'business' | 'first';
  budget?: number;
  preferences?: TravelPreferences;
  timestamp: string;
}

export interface TravelPreferences {
  accommodation?: AccommodationPreferences;
  flight?: FlightPreferences;
  activities?: string[];
  dietary?: string[];
  accessibility?: string[];
}

export interface AccommodationPreferences {
  type?: 'hotel' | 'apartment' | 'hostel' | 'resort';
  rating?: number;
  amenities?: string[];
  location?: string;
}

export interface FlightPreferences {
  airline?: string;
  maxStops?: number;
  preferredDepartureTime?: string;
  seatPreference?: string;
}

// Chat and conversation types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: ChatMessageMetadata;
}

// Chat response can be either from session creation or regular chat
export type ChatResponse = ChatMessageResponse | SessionCreationResponse;

export interface ChatMessageResponse {
  message: string;
  updated_context?: any;
  suggestions?: string[];
  search_triggered?: boolean;
  conflicts?: any[];
  chat_history?: ChatMessage[];
  hints?: any[];
  conversation_state?: string;
  extracted_entities?: any[];
  next_steps?: string[];
  searchResults?: SearchResults;
  context?: any;
}

export interface SessionCreationResponse {
  session_id: string;
  initial_response: string;
  parsed_intent?: any;
  suggestions?: string[];
  trip_context?: any;
  status?: string;
  metadata?: {
    suggestions?: string[];
    hints?: any[];
    conversation_state?: string;
    extracted_entities?: any[];
    next_steps?: string[];
  };
}

export interface ChatMessageMetadata {
  searchResults?: SearchResults;
  suggestions?: string[];
  orchestrator_suggestions?: string[];
  clarifying_questions?: string[];
  hints?: any[];
  actionRequired?: boolean;
  context?: any;
  trip_plan_created?: boolean;
  trip_plan?: {
    id: string;
    name: string;
    destination: string;
    departure_date?: string;
    return_date?: string;
    travelers?: number;
    status?: string;
    saved_items?: any[];
  };
  trip_plan_intent?: {
    wants_trip_plan: boolean;
    confidence: number;
    reason: string;
    trip_info?: any;
  };
}

// Search results types
export interface SearchResults {
  flights?: FlightOption[];
  hotels?: HotelOption[];
  activities?: ActivityOption[];
  summary?: string;
}

export interface FlightOption {
  id: string;
  airline: string;
  flightNumber: string;
  origin: Airport;
  destination: Airport;
  departureTime: string;
  arrivalTime: string;
  duration: string;
  price: Price;
  stops: number;
  aircraft?: string;
  amenities?: string[];
}

export interface HotelOption {
  id: string;
  name: string;
  rating: number;
  price: Price;
  location: Location;
  amenities: string[];
  images?: string[];
  description?: string;
  reviewScore?: number;
  reviewCount?: number;
}

export interface ActivityOption {
  id: string;
  name: string;
  type: string;
  description: string;
  price: Price;
  location: Location;
  duration?: string;
  rating?: number;
  images?: string[];
}

// Common types
export interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
  terminal?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export interface Location {
  address: string;
  city: string;
  country: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export interface Price {
  amount: number;
  currency: string;
  displayPrice: string;
}

// Session and context types
export interface TravelSession {
  id: string;
  userId?: string;
  messages: ChatMessage[];
  context: TravelContext;
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'completed' | 'archived';
}

export interface TravelContext {
  currentRequest?: TravelRequest;
  searchHistory: TravelRequest[];
  selectedOptions: {
    flights?: FlightOption[];
    hotels?: HotelOption[];
    activities?: ActivityOption[];
  };
  trip?: Trip;
}

// Trip management types
export interface Trip {
  id: string;
  name: string;
  description?: string;
  destination: string;
  startDate: string;
  endDate: string;
  travelers: TravelerProfile[];
  itinerary: ItineraryItem[];
  budget?: number;
  status: 'planning' | 'booked' | 'completed' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}

export interface ItineraryItem {
  id: string;
  type: 'flight' | 'hotel' | 'activity' | 'transport' | 'meal';
  title: string;
  description?: string;
  startTime: string;
  endTime?: string;
  location?: Location;
  price?: Price;
  bookingReference?: string;
  status: 'planned' | 'booked' | 'completed' | 'cancelled';
}

export interface TravelerProfile {
  id: string;
  name: string;
  email?: string;
  dateOfBirth?: string;
  nationality?: string;
  passportNumber?: string;
  preferences?: TravelPreferences;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  metadata?: any;
}


// UI state types
export interface UIState {
  isLoading: boolean;
  sidebarOpen: boolean;
  activeTab: 'flights' | 'hotels' | 'activities' | 'trip';
  selectedItems: SelectedItems;
}

export interface SelectedItems {
  flights: string[];
  hotels: string[];
  activities: string[];
}