export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin?: boolean;
  avatar?: string;
  preferences?: UserPreferences;
  created_at?: string;
  updated_at?: string;
}

export interface UserPreferences {
  currency: string;
  language: string;
  timezone: string;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
  travel: TravelUserPreferences;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  tripUpdates: boolean;
  priceAlerts: boolean;
  marketing: boolean;
}

export interface PrivacySettings {
  shareTrips: boolean;
  publicProfile: boolean;
  dataCollection: boolean;
}

export interface TravelUserPreferences {
  defaultTravelClass: 'economy' | 'premium_economy' | 'business' | 'first';
  preferredAirlines: string[];
  preferredHotelBrands: string[];
  dietaryRestrictions: string[];
  accessibilityNeeds: string[];
  loyaltyPrograms: LoyaltyProgram[];
}

export interface LoyaltyProgram {
  provider: string;
  membershipNumber: string;
  tier?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}