// Main types exports
export * from './User';
export * from './TravelRequestTypes';

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