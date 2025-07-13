/**
 * Mock data generators for testing.
 * 
 * Provides factory functions and mock data for various entities
 * used throughout the Pathavana application.
 */

import { faker } from '@faker-js/faker';

// User mock data
export const createMockUser = (overrides: any = {}) => ({
  id: faker.number.int({ min: 1, max: 10000 }),
  email: faker.internet.email(),
  full_name: faker.person.fullName(),
  first_name: faker.person.firstName(),
  last_name: faker.person.lastName(),
  phone: faker.phone.number(),
  email_verified: faker.datatype.boolean(),
  status: faker.helpers.arrayElement(['active', 'pending', 'suspended']),
  profile_picture_url: faker.image.avatar(),
  created_at: faker.date.past().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  last_login_at: faker.date.recent().toISOString(),
  ...overrides,
});

// Travel session mock data
export const createMockTravelSession = (overrides: any = {}) => ({
  session_id: faker.string.uuid(),
  user_id: faker.number.int({ min: 1, max: 1000 }),
  status: faker.helpers.arrayElement(['active', 'planning', 'completed', 'archived']),
  session_data: {
    messages: [
      {
        role: 'user',
        content: `I want to plan a trip to ${faker.location.city()}`,
        timestamp: faker.date.recent().toISOString(),
      },
      {
        role: 'assistant',
        content: `I'd be happy to help you plan your trip to ${faker.location.city()}!`,
        timestamp: faker.date.recent().toISOString(),
      },
    ],
    parsed_intent: {
      destination: faker.location.city(),
      travel_type: faker.helpers.arrayElement(['leisure', 'business', 'adventure', 'family']),
      travelers: faker.number.int({ min: 1, max: 8 }),
      confidence: faker.number.float({ min: 0.7, max: 1.0 }),
    },
  },
  plan_data: {
    destination: `${faker.location.city()}, ${faker.location.country()}`,
    departure_date: faker.date.future({ years: 1 }).toISOString().split('T')[0],
    return_date: faker.date.future({ years: 1 }).toISOString().split('T')[0],
    travelers: faker.number.int({ min: 1, max: 8 }),
    budget: faker.number.int({ min: 1000, max: 10000 }),
  },
  created_at: faker.date.past().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  last_activity_at: faker.date.recent().toISOString(),
  ...overrides,
});

// Flight mock data
export const createMockFlight = (overrides: any = {}) => ({
  id: faker.string.uuid(),
  origin: faker.airline.airport().iataCode,
  destination: faker.airline.airport().iataCode,
  departure_date: faker.date.future().toISOString().split('T')[0],
  return_date: faker.date.future().toISOString().split('T')[0],
  airline: faker.airline.airline().name,
  flight_number: `${faker.string.alpha({ length: 2, casing: 'upper' })}${faker.number.int({ min: 100, max: 9999 })}`,
  price: {
    total: faker.number.int({ min: 200, max: 3000 }),
    currency: faker.finance.currencyCode(),
    base_fare: faker.number.int({ min: 150, max: 2500 }),
    taxes: faker.number.int({ min: 50, max: 500 }),
  },
  duration: `${faker.number.int({ min: 2, max: 15 })}h ${faker.number.int({ min: 0, max: 59 })}m`,
  stops: faker.number.int({ min: 0, max: 3 }),
  cabin_class: faker.helpers.arrayElement(['economy', 'premium_economy', 'business', 'first']),
  departure_time: faker.date.future().toISOString(),
  arrival_time: faker.date.future().toISOString(),
  aircraft: faker.helpers.arrayElement(['Boeing 737', 'Airbus A320', 'Boeing 777', 'Airbus A350']),
  ...overrides,
});

// Hotel mock data
export const createMockHotel = (overrides: any = {}) => ({
  id: faker.string.uuid(),
  name: `${faker.company.name()} Hotel`,
  description: faker.lorem.sentences(3),
  location: {
    address: faker.location.streetAddress(),
    city: faker.location.city(),
    country: faker.location.country(),
    latitude: faker.location.latitude(),
    longitude: faker.location.longitude(),
    district: faker.location.secondaryAddress(),
  },
  check_in: faker.date.future().toISOString().split('T')[0],
  check_out: faker.date.future().toISOString().split('T')[0],
  room_type: faker.helpers.arrayElement([
    'Standard Room',
    'Superior Room',
    'Deluxe Room',
    'Suite',
    'Executive Suite',
  ]),
  price: {
    total: faker.number.int({ min: 80, max: 800 }),
    currency: faker.finance.currencyCode(),
    per_night: faker.number.int({ min: 80, max: 400 }),
    nights: faker.number.int({ min: 1, max: 14 }),
    taxes: faker.number.int({ min: 10, max: 100 }),
  },
  rating: faker.number.float({ min: 3.0, max: 5.0, precision: 0.1 }),
  amenities: faker.helpers.arrayElements([
    'WiFi',
    'Breakfast',
    'Gym',
    'Pool',
    'Spa',
    'Parking',
    'Restaurant',
    'Bar',
    'Concierge',
    'Room Service',
    'Air Conditioning',
    'Pet Friendly',
  ], { min: 3, max: 8 }),
  images: Array.from({ length: faker.number.int({ min: 3, max: 10 }) }, () => 
    faker.image.urlLoremFlickr({ category: 'hotel' })
  ),
  cancellation_policy: faker.helpers.arrayElement([
    'Free cancellation',
    'Free cancellation until 24h before',
    'Free cancellation until 48h before',
    'Non-refundable',
  ]),
  ...overrides,
});

// Activity mock data
export const createMockActivity = (overrides: any = {}) => ({
  id: faker.string.uuid(),
  name: faker.lorem.words(3),
  description: faker.lorem.sentences(2),
  location: {
    name: faker.location.city(),
    address: faker.location.streetAddress(),
    latitude: faker.location.latitude(),
    longitude: faker.location.longitude(),
  },
  date: faker.date.future().toISOString().split('T')[0],
  time: faker.date.future().toTimeString().split(' ')[0].slice(0, 5),
  duration: faker.number.int({ min: 30, max: 480 }), // minutes
  price: {
    total: faker.number.int({ min: 20, max: 300 }),
    currency: faker.finance.currencyCode(),
    per_person: faker.number.int({ min: 20, max: 300 }),
    persons: faker.number.int({ min: 1, max: 8 }),
  },
  category: faker.helpers.arrayElement([
    'sightseeing',
    'cultural',
    'adventure',
    'food',
    'entertainment',
    'outdoor',
    'historical',
  ]),
  difficulty: faker.helpers.arrayElement(['easy', 'moderate', 'challenging']),
  languages: faker.helpers.arrayElements(['English', 'French', 'Spanish', 'German', 'Italian'], { min: 1, max: 3 }),
  inclusions: faker.helpers.arrayElements([
    'Guide',
    'Transportation',
    'Equipment',
    'Refreshments',
    'Photos',
    'Certificate',
  ], { min: 1, max: 4 }),
  rating: faker.number.float({ min: 3.0, max: 5.0, precision: 0.1 }),
  reviews_count: faker.number.int({ min: 5, max: 500 }),
  images: Array.from({ length: faker.number.int({ min: 2, max: 6 }) }, () => 
    faker.image.urlLoremFlickr({ category: 'travel' })
  ),
  ...overrides,
});

// Booking mock data
export const createMockBooking = (overrides: any = {}) => ({
  id: faker.number.int({ min: 1, max: 10000 }),
  session_id: faker.string.uuid(),
  booking_type: faker.helpers.arrayElement(['flight', 'hotel', 'activity', 'package']),
  provider: faker.helpers.arrayElement(['amadeus', 'booking.com', 'viator', 'expedia']),
  provider_booking_id: faker.string.alphanumeric(10).toUpperCase(),
  confirmation_code: faker.string.alphanumeric(6).toUpperCase(),
  booking_status: faker.helpers.arrayElement(['pending', 'confirmed', 'cancelled', 'completed']),
  payment_status: faker.helpers.arrayElement(['pending', 'paid', 'failed', 'refunded']),
  total_amount: faker.number.int({ min: 5000, max: 500000 }), // in cents
  currency: faker.finance.currencyCode(),
  booking_date: faker.date.past().toISOString(),
  travel_date: faker.date.future().toISOString(),
  created_at: faker.date.past().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  ...overrides,
});

// Traveler mock data
export const createMockTraveler = (overrides: any = {}) => ({
  id: faker.number.int({ min: 1, max: 10000 }),
  user_id: faker.number.int({ min: 1, max: 1000 }),
  first_name: faker.person.firstName(),
  last_name: faker.person.lastName(),
  middle_name: faker.person.middleName(),
  email: faker.internet.email(),
  phone: faker.phone.number(),
  date_of_birth: faker.date.birthdate().toISOString().split('T')[0],
  gender: faker.helpers.arrayElement(['male', 'female', 'other']),
  nationality: faker.location.countryCode(),
  passport_number: faker.string.alphanumeric(9).toUpperCase(),
  passport_country: faker.location.countryCode(),
  passport_expiry: faker.date.future({ years: 5 }).toISOString().split('T')[0],
  emergency_contact: {
    name: faker.person.fullName(),
    relationship: faker.helpers.arrayElement(['spouse', 'parent', 'sibling', 'friend']),
    phone: faker.phone.number(),
    email: faker.internet.email(),
  },
  dietary_restrictions: faker.helpers.arrayElements([
    'vegetarian',
    'vegan',
    'gluten-free',
    'kosher',
    'halal',
    'lactose-free',
  ], { min: 0, max: 2 }),
  accessibility_needs: faker.helpers.arrayElements([
    'wheelchair',
    'visual_impairment',
    'hearing_impairment',
    'mobility_assistance',
  ], { min: 0, max: 1 }),
  known_traveler_number: faker.string.numeric(11),
  global_entry_number: faker.string.numeric(8),
  created_at: faker.date.past().toISOString(),
  updated_at: faker.date.recent().toISOString(),
  ...overrides,
});

// API response mock data
export const createMockApiResponse = (data: any, success = true) => ({
  ok: success,
  status: success ? 200 : 400,
  json: async () => success ? data : { detail: 'API Error' },
  text: async () => JSON.stringify(success ? data : { detail: 'API Error' }),
});

// Error mock data
export const createMockError = (message = 'Something went wrong', status = 500) => {
  const error = new Error(message) as any;
  error.response = {
    status,
    data: { detail: message },
  };
  return error;
};

// Pagination mock data
export const createMockPagination = (totalItems = 100, page = 1, limit = 10) => ({
  total: totalItems,
  page,
  limit,
  pages: Math.ceil(totalItems / limit),
  has_next: page < Math.ceil(totalItems / limit),
  has_prev: page > 1,
});

// Search metadata mock data
export const createMockSearchMetadata = (overrides: any = {}) => ({
  search_id: faker.string.uuid(),
  total_results: faker.number.int({ min: 1, max: 1000 }),
  search_time: faker.number.float({ min: 0.1, max: 5.0, precision: 0.01 }),
  cached: faker.datatype.boolean(),
  filters_applied: faker.helpers.arrayElements([
    'price_range',
    'duration',
    'rating',
    'amenities',
    'location',
  ], { min: 0, max: 3 }),
  sort_by: faker.helpers.arrayElement(['price', 'rating', 'duration', 'popularity']),
  sort_order: faker.helpers.arrayElement(['asc', 'desc']),
  ...overrides,
});

// Batch data generators
export const createMockUsers = (count = 5) => 
  Array.from({ length: count }, () => createMockUser());

export const createMockTravelSessions = (count = 5) => 
  Array.from({ length: count }, () => createMockTravelSession());

export const createMockFlights = (count = 10) => 
  Array.from({ length: count }, () => createMockFlight());

export const createMockHotels = (count = 10) => 
  Array.from({ length: count }, () => createMockHotel());

export const createMockActivities = (count = 10) => 
  Array.from({ length: count }, () => createMockActivity());

export const createMockBookings = (count = 5) => 
  Array.from({ length: count }, () => createMockBooking());

export const createMockTravelers = (count = 3) => 
  Array.from({ length: count }, () => createMockTraveler());

// Common mock responses
export const mockResponses = {
  auth: {
    login: {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: createMockUser(),
    },
    register: {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: createMockUser({ email_verified: false }),
    },
    refreshToken: {
      access_token: 'new-mock-access-token',
      refresh_token: 'new-mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
    },
  },
  
  travel: {
    sessions: {
      sessions: createMockTravelSessions(3),
      total: 3,
      pagination: createMockPagination(3, 1, 10),
    },
    
    flightSearch: {
      flights: createMockFlights(15),
      search_metadata: createMockSearchMetadata(),
    },
    
    hotelSearch: {
      hotels: createMockHotels(20),
      search_metadata: createMockSearchMetadata(),
    },
    
    activitySearch: {
      activities: createMockActivities(25),
      search_metadata: createMockSearchMetadata(),
    },
  },
  
  bookings: {
    list: {
      bookings: createMockBookings(5),
      total: 5,
      pagination: createMockPagination(5, 1, 10),
    },
  },
  
  travelers: {
    list: {
      travelers: createMockTravelers(3),
      total: 3,
    },
  },
};

// Default export with all factories
export default {
  createMockUser,
  createMockTravelSession,
  createMockFlight,
  createMockHotel,
  createMockActivity,
  createMockBooking,
  createMockTraveler,
  createMockApiResponse,
  createMockError,
  createMockPagination,
  createMockSearchMetadata,
  createMockUsers,
  createMockTravelSessions,
  createMockFlights,
  createMockHotels,
  createMockActivities,
  createMockBookings,
  createMockTravelers,
  mockResponses,
};