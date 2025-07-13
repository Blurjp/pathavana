import { apiClient } from './api';
import { 
  Trip, 
  TravelerProfile, 
  FlightOption, 
  HotelOption,
  ApiResponse 
} from '../types';

export class TravelApi {
  // Trip management
  async getTrips(): Promise<ApiResponse<Trip[]>> {
    return apiClient.get('/api/trips');
  }

  async getTrip(tripId: string): Promise<ApiResponse<Trip>> {
    return apiClient.get(`/api/trips/${tripId}`);
  }

  async createTrip(trip: Partial<Trip>): Promise<ApiResponse<Trip>> {
    return apiClient.post('/api/trips', trip);
  }

  async updateTrip(tripId: string, updates: Partial<Trip>): Promise<ApiResponse<Trip>> {
    return apiClient.put(`/api/trips/${tripId}`, updates);
  }

  async deleteTrip(tripId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/api/trips/${tripId}`);
  }

  // Traveler profiles
  async getTravelers(): Promise<ApiResponse<TravelerProfile[]>> {
    return apiClient.get('/api/travelers');
  }

  async getTraveler(travelerId: string): Promise<ApiResponse<TravelerProfile>> {
    return apiClient.get(`/api/travelers/${travelerId}`);
  }

  async createTraveler(traveler: Partial<TravelerProfile>): Promise<ApiResponse<TravelerProfile>> {
    return apiClient.post('/api/travelers', traveler);
  }

  async updateTraveler(
    travelerId: string, 
    updates: Partial<TravelerProfile>
  ): Promise<ApiResponse<TravelerProfile>> {
    return apiClient.put(`/api/travelers/${travelerId}`, updates);
  }

  async deleteTraveler(travelerId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/api/travelers/${travelerId}`);
  }

  // Booking operations
  async bookFlight(
    flightId: string, 
    travelers: TravelerProfile[]
  ): Promise<ApiResponse<any>> {
    return apiClient.post('/api/v1/bookings/flights', {
      flightId,
      travelers
    });
  }

  async bookHotel(
    hotelId: string, 
    checkIn: string, 
    checkOut: string,
    guests: number
  ): Promise<ApiResponse<any>> {
    return apiClient.post('/api/v1/bookings/hotels', {
      hotelId,
      checkIn,
      checkOut,
      guests
    });
  }

  // Price monitoring
  async createPriceAlert(
    flightId: string, 
    targetPrice: number
  ): Promise<ApiResponse<any>> {
    return apiClient.post('/api/v1/price-alerts', {
      flightId,
      targetPrice
    });
  }

  async getPriceAlerts(): Promise<ApiResponse<any[]>> {
    return apiClient.get('/api/v1/price-alerts');
  }

  // Destination information
  async getDestinationInfo(destination: string): Promise<ApiResponse<any>> {
    return apiClient.get(`/api/v1/destinations/${destination}`);
  }

  async getWeatherInfo(
    destination: string, 
    date: string
  ): Promise<ApiResponse<any>> {
    return apiClient.get(`/api/v1/weather/${destination}`, {
      date
    });
  }
}

export const travelApi = new TravelApi();