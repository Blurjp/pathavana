import { apiClient } from './api';
import { ApiResponse } from '../types';

export interface UserProfileResponse {
  id: number;
  email: string;
  full_name: string;
  first_name: string;
  last_name: string;
  phone?: string;
  profile_picture_url?: string;
  created_at?: string;
  profile?: {
    date_of_birth?: string;
    gender?: string;
    nationality?: string;
    country_of_residence?: string;
    city?: string;
    timezone?: string;
    preferred_language?: string;
    preferred_currency?: string;
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    emergency_contact_relationship?: string;
  };
  preferences?: {
    preferred_cabin_class?: string;
    preferred_airlines?: string[];
    avoided_airlines?: string[];
    preferred_seat_type?: string;
    preferred_hotel_class?: string;
    preferred_hotel_chains?: string[];
    activity_interests?: string[];
    dietary_restrictions?: string[];
    mobility_requirements?: string[];
    default_budget_range?: {
      min?: number;
      max?: number;
      currency?: string;
    };
    budget_currency?: string;
  };
}

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  profile?: {
    date_of_birth?: string;
    gender?: string;
    nationality?: string;
    country_of_residence?: string;
    city?: string;
    timezone?: string;
    preferred_language?: string;
    preferred_currency?: string;
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    emergency_contact_relationship?: string;
  };
  preferences?: {
    preferred_cabin_class?: string;
    preferred_airlines?: string[];
    avoided_airlines?: string[];
    preferred_seat_type?: string;
    preferred_hotel_class?: string;
    preferred_hotel_chains?: string[];
    activity_interests?: string[];
    dietary_restrictions?: string[];
    mobility_requirements?: string[];
    default_budget_range?: {
      min?: number;
      max?: number;
      currency?: string;
    };
    budget_currency?: string;
  };
}

export const profileApi = {
  // Get current user's profile
  getProfile: async (): Promise<ApiResponse<UserProfileResponse>> => {
    try {
      const response = await apiClient.get<UserProfileResponse>('/api/v1/users/profile');
      return response;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  },

  // Update current user's profile
  updateProfile: async (updates: UserProfileUpdate): Promise<ApiResponse<UserProfileResponse>> => {
    try {
      const response = await apiClient.put<UserProfileResponse>('/api/v1/users/profile', updates);
      return response;
    } catch (error) {
      console.error('Error updating user profile:', error);
      throw error;
    }
  }
};