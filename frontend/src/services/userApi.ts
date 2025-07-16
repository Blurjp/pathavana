import apiClient from './api';
import { UserProfile } from '../hooks/useUserProfile';

export interface UpdateProfileData {
  firstName?: string;
  lastName?: string;
  phone?: string;
  dateOfBirth?: string;
  location?: string;
  bio?: string;
  avatar?: string;
  preferences?: Partial<UserProfile['preferences']>;
}

export const getUserProfile = async (userId: number): Promise<UserProfile> => {
  const response = await apiClient.get<UserProfile>(`/api/users/${userId}/profile`);
  
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to fetch user profile');
  }
  
  return response.data;
};

export const updateUserProfile = async (
  userId: number,
  data: UpdateProfileData
): Promise<UserProfile> => {
  const response = await apiClient.put<UserProfile>(`/api/users/${userId}/profile`, data);
  
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to update user profile');
  }
  
  return response.data;
};

export const uploadAvatar = async (userId: number, file: File): Promise<{ avatarUrl: string }> => {
  const formData = new FormData();
  formData.append('avatar', file);
  
  const response = await apiClient.upload<{ avatarUrl: string }>(
    `/api/users/${userId}/avatar`,
    formData
  );
  
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to upload avatar');
  }
  
  return response.data;
};

export const updateUserPreferences = async (
  userId: number,
  preferences: Partial<UserProfile['preferences']>
): Promise<UserProfile> => {
  const response = await apiClient.put<UserProfile>(
    `/api/users/${userId}/preferences`,
    { preferences }
  );
  
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to update preferences');
  }
  
  return response.data;
};

export const deleteUserAccount = async (userId: number): Promise<void> => {
  const response = await apiClient.delete<void>(`/api/users/${userId}`);
  
  if (!response.success) {
    throw new Error(response.error || 'Failed to delete account');
  }
};