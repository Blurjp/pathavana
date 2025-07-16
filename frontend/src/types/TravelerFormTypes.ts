// Legacy traveler form types - used by existing form components
// These will need to be mapped to the backend API format

export interface LegacyTravelPreferences {
  accommodation?: {
    type?: string;
    rating?: number;
    amenities?: string[];
    location?: string;
  };
  flight?: {
    airline?: string;
    maxStops?: number;
    preferredDepartureTime?: string;
    seatPreference?: string;
  };
  activities?: string[];
  dietary?: string[];
  accessibility?: string[];
}

export interface LegacyTravelerProfile {
  id?: string;
  name: string;
  email?: string;
  dateOfBirth?: string;
  nationality?: string;
  passportNumber?: string;
  preferences?: LegacyTravelPreferences;
}

// Adapter functions to convert between legacy and new formats
export function legacyToNewTraveler(legacy: Partial<LegacyTravelerProfile>): any {
  // Split name into first and last name
  const nameParts = (legacy.name || '').trim().split(' ');
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';

  return {
    id: legacy.id,
    first_name: firstName,
    last_name: lastName,
    email: legacy.email,
    date_of_birth: legacy.dateOfBirth,
    nationality: legacy.nationality,
    // passport_number would go to a separate document entity
    preferences: legacy.preferences ? {
      flight: {
        seatPreference: legacy.preferences.flight?.seatPreference,
        preferredDepartureTime: legacy.preferences.flight?.preferredDepartureTime,
      },
      general: {
        dietaryRestrictions: legacy.preferences.dietary,
        accessibilityNeeds: legacy.preferences.accessibility,
      }
    } : undefined,
    dietary_restrictions: legacy.preferences?.dietary,
    accessibility_needs: legacy.preferences?.accessibility,
  };
}

export function newToLegacyTraveler(traveler: any): LegacyTravelerProfile {
  return {
    id: traveler.id,
    name: `${traveler.first_name || ''} ${traveler.last_name || ''}`.trim(),
    email: traveler.email,
    dateOfBirth: traveler.date_of_birth,
    nationality: traveler.nationality,
    // passport would come from documents
    preferences: {
      flight: {
        seatPreference: traveler.preferences?.flight?.seatPreference,
        preferredDepartureTime: traveler.preferences?.flight?.preferredDepartureTime,
      },
      dietary: traveler.dietary_restrictions || [],
      accessibility: traveler.accessibility_needs || [],
    }
  };
}