import { apiClient } from './api';
import { TravelerProfile, ApiResponse } from '../types';

export const travelersApi = {
  // Get all travelers for the authenticated user
  getTravelers: async (): Promise<ApiResponse<TravelerProfile[]>> => {
    try {
      const response = await apiClient.get<TravelerProfile[]>('/api/v1/travelers/');
      return response;
    } catch (error) {
      console.error('Error fetching travelers:', error);
      throw error;
    }
  },

  // Get a specific traveler by ID
  getTraveler: async (travelerId: string): Promise<ApiResponse<TravelerProfile>> => {
    try {
      const response = await apiClient.get<TravelerProfile>(`/api/v1/travelers/${travelerId}`);
      return response;
    } catch (error) {
      console.error('Error fetching traveler:', error);
      throw error;
    }
  },

  // Create a new traveler
  createTraveler: async (traveler: Partial<TravelerProfile>): Promise<ApiResponse<TravelerProfile>> => {
    try {
      const response = await apiClient.post<TravelerProfile>('/api/v1/travelers/', traveler);
      return response;
    } catch (error) {
      console.error('Error creating traveler:', error);
      throw error;
    }
  },

  // Update an existing traveler
  updateTraveler: async (
    travelerId: string,
    updates: Partial<TravelerProfile>
  ): Promise<ApiResponse<TravelerProfile>> => {
    try {
      const response = await apiClient.put<TravelerProfile>(`/api/v1/travelers/${travelerId}`, updates);
      return response;
    } catch (error) {
      console.error('Error updating traveler:', error);
      throw error;
    }
  },

  // Delete a traveler
  deleteTraveler: async (travelerId: string): Promise<ApiResponse<void>> => {
    try {
      const response = await apiClient.delete<void>(`/api/v1/travelers/${travelerId}`);
      return response;
    } catch (error) {
      console.error('Error deleting traveler:', error);
      throw error;
    }
  },

  // Add travelers to a trip
  addTravelersToTrip: async (
    tripId: string,
    travelerIds: string[]
  ): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.post<any>(`/api/trips/${tripId}/travelers`, {
        travelerIds
      });
      return response;
    } catch (error) {
      console.error('Error adding travelers to trip:', error);
      throw error;
    }
  },

  // Remove a traveler from a trip
  removeTravelerFromTrip: async (
    tripId: string,
    travelerId: string
  ): Promise<ApiResponse<void>> => {
    try {
      const response = await apiClient.delete<void>(`/api/trips/${tripId}/travelers/${travelerId}`);
      return response;
    } catch (error) {
      console.error('Error removing traveler from trip:', error);
      throw error;
    }
  }
};