import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getUserProfile, updateUserProfile } from '../services/userApi';

export interface UserProfile {
  id: number;
  email: string;
  emailVerified?: boolean;
  firstName?: string;
  lastName?: string;
  full_name: string;
  phone?: string;
  dateOfBirth?: string;
  location?: string;
  bio?: string;
  avatar?: string;
  preferences?: {
    travelStyle: string[];
    budget: string;
    accommodationType: string[];
    interests: string[];
    dietaryRestrictions: string[];
    accessibility: string[];
    travelPace: string;
    groupSize: string;
    preferredAirlines: string[];
    preferredHotelChains: string[];
  };
  created_at?: string;
  updated_at?: string;
}

interface UseUserProfileReturn {
  profile: UserProfile | null;
  loading: boolean;
  error: string | null;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const useUserProfile = (): UseUserProfileReturn => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    if (!user?.id) {
      setProfile(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await getUserProfile(user.id);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch profile');
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const updateProfile = useCallback(async (data: Partial<UserProfile>) => {
    if (!user?.id || !profile) {
      throw new Error('No user profile to update');
    }

    try {
      setError(null);
      const updatedProfile = await updateUserProfile(user.id, data);
      setProfile(updatedProfile);
      
      // Profile is already updated from the API response above
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [user?.id, profile]);

  const refreshProfile = useCallback(async () => {
    await fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    updateProfile,
    refreshProfile,
  };
};

export default useUserProfile;