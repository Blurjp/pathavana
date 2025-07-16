// Traveler-related types

export interface TravelerPreferences {
  flight?: {
    seatPreference?: string;
    preferredDepartureTime?: string;
    mealPreference?: string;
  };
  hotel?: {
    bedType?: string;
    roomType?: string;
    floorPreference?: string;
  };
  general?: {
    dietaryRestrictions?: string[];
    accessibilityNeeds?: string[];
    specialRequests?: string;
  };
}

// For creating/editing travelers (id is optional)
export interface TravelerFormData {
  id?: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  full_name?: string;
  date_of_birth?: string;
  gender?: string;
  nationality?: string;
  country_of_residence?: string;
  email?: string;
  phone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  relationship_to_user?: string;
  dietary_restrictions?: string[];
  accessibility_needs?: string[];
  medical_conditions?: string[];
  frequent_flyer_numbers?: Record<string, string>;
  hotel_loyalty_numbers?: Record<string, string>;
  known_traveler_numbers?: Record<string, string>;
  passport_verified?: boolean;
  document_status?: string;
  preferences?: TravelerPreferences;
  created_at?: string;
  updated_at?: string;
}

// For displaying travelers (id is required)
export interface TravelerProfile extends TravelerFormData {
  id: string; // Override to make required
}

export interface TravelerDocument {
  id?: string;
  traveler_id: string;
  document_type: 'passport' | 'national_id' | 'drivers_license' | 'visa' | 'vaccination_card' | 'other';
  document_number: string;
  issuing_country: string;
  issue_date?: string;
  expiry_date?: string;
  issuing_authority?: string;
  is_primary?: boolean;
  notes?: string;
}

export interface TravelerListResponse {
  travelers: TravelerProfile[];
  total_count: number;
  skip: number;
  limit: number;
}