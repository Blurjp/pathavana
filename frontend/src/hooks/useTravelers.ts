import { useState, useEffect, useCallback } from 'react';
import { TravelerProfile } from '../types';
import { travelersApi } from '../services/travelersApi';
import { handleApiError } from '../utils/errorHandler';

interface UseTravelersReturn {
  travelers: TravelerProfile[];
  isLoading: boolean;
  error: string | null;
  createTraveler: (data: Partial<TravelerProfile>) => Promise<TravelerProfile>;
  updateTraveler: (id: string, data: Partial<TravelerProfile>) => Promise<TravelerProfile>;
  deleteTraveler: (id: string) => Promise<void>;
  refreshTravelers: () => Promise<void>;
}

export const useTravelers = (): UseTravelersReturn => {
  const [travelers, setTravelers] = useState<TravelerProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTravelers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await travelersApi.getTravelers();
      if (response.success && response.data) {
        setTravelers(response.data);
      } else {
        throw new Error(response.error || 'Failed to load travelers');
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err, 'load_travelers');
      setError(errorMessage);
      console.error('Failed to load travelers:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTravelers();
  }, [loadTravelers]);

  const createTraveler = async (data: Partial<TravelerProfile>): Promise<TravelerProfile> => {
    setError(null);
    
    try {
      const response = await travelersApi.createTraveler(data);
      if (response.success && response.data) {
        setTravelers(prev => [...prev, response.data!]);
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create traveler');
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err, 'create_traveler');
      setError(errorMessage);
      throw err;
    }
  };

  const updateTraveler = async (id: string, data: Partial<TravelerProfile>): Promise<TravelerProfile> => {
    setError(null);
    
    try {
      const response = await travelersApi.updateTraveler(id, data);
      if (response.success && response.data) {
        setTravelers(prev => prev.map(t => t.id === id ? response.data! : t));
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to update traveler');
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err, 'update_traveler');
      setError(errorMessage);
      throw err;
    }
  };

  const deleteTraveler = async (id: string): Promise<void> => {
    setError(null);
    
    try {
      const response = await travelersApi.deleteTraveler(id);
      if (response.success) {
        setTravelers(prev => prev.filter(t => t.id !== id));
      } else {
        throw new Error(response.error || 'Failed to delete traveler');
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err, 'delete_traveler');
      setError(errorMessage);
      throw err;
    }
  };

  const refreshTravelers = async (): Promise<void> => {
    await loadTravelers();
  };

  return {
    travelers,
    isLoading,
    error,
    createTraveler,
    updateTraveler,
    deleteTraveler,
    refreshTravelers
  };
};