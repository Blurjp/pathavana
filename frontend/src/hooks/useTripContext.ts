import { useState, useEffect, useCallback } from 'react';
import { TravelRequest, TravelContext, Trip, ItineraryItem, Location } from '../types';
import { unifiedTravelApi } from '../services/unifiedTravelApi';

interface UseTripContextReturn {
  context: TravelContext | null;
  isLoading: boolean;
  error: string | null;
  updateCurrentRequest: (updates: Partial<TravelRequest>) => void;
  addToTrip: (item: ItineraryItem) => void;
  removeFromTrip: (itemId: string) => void;
  updateTrip: (updates: Partial<Trip>) => void;
  clearContext: () => Promise<void>;
  saveContext: () => Promise<boolean>;
  detectConflicts: (newData: Partial<TravelRequest>) => string[];
  resolveConflicts: (resolution: 'keep_existing' | 'use_new' | 'merge') => void;
}

export const useTripContext = (sessionId?: string): UseTripContextReturn => {
  const [context, setContext] = useState<TravelContext | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingUpdates, setPendingUpdates] = useState<Partial<TravelRequest> | null>(null);

  // Load context when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadContext(sessionId);
    }
  }, [sessionId]);

  const loadContext = async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await unifiedTravelApi.getContext(sessionId);
      if (response.success && response.data) {
        setContext(response.data);
      } else {
        // Initialize with default context
        setContext({
          currentRequest: undefined,
          searchHistory: [],
          selectedOptions: {
            flights: [],
            hotels: [],
            activities: [],
          },
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load context');
      // Initialize with default context on error
      setContext({
        currentRequest: undefined,
        searchHistory: [],
        selectedOptions: {
          flights: [],
          hotels: [],
          activities: [],
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateCurrentRequest = useCallback((updates: Partial<TravelRequest>) => {
    setContext(prev => {
      if (!prev) return null;

      const newRequest = {
        ...prev.currentRequest,
        ...updates,
        timestamp: new Date().toISOString(),
      } as TravelRequest;

      return {
        ...prev,
        currentRequest: newRequest,
        searchHistory: [
          ...prev.searchHistory.filter(req => req.id !== newRequest.id),
          newRequest,
        ].slice(-20), // Keep last 20 requests
      };
    });
  }, []);

  const addToTrip = useCallback((item: ItineraryItem) => {
    setContext(prev => {
      if (!prev) return null;

      const trip = prev.trip || createDefaultTrip(prev.currentRequest);
      const updatedTrip = {
        ...trip,
        itinerary: [...trip.itinerary, item],
        updatedAt: new Date().toISOString(),
      };

      return {
        ...prev,
        trip: updatedTrip,
      };
    });
  }, []);

  const removeFromTrip = useCallback((itemId: string) => {
    setContext(prev => {
      if (!prev?.trip) return prev;

      const updatedTrip = {
        ...prev.trip,
        itinerary: prev.trip.itinerary.filter(item => item.id !== itemId),
        updatedAt: new Date().toISOString(),
      };

      return {
        ...prev,
        trip: updatedTrip,
      };
    });
  }, []);

  const updateTrip = useCallback((updates: Partial<Trip>) => {
    setContext(prev => {
      if (!prev?.trip) return prev;

      const updatedTrip = {
        ...prev.trip,
        ...updates,
        updatedAt: new Date().toISOString(),
      };

      return {
        ...prev,
        trip: updatedTrip,
      };
    });
  }, []);

  const clearContext = useCallback(async () => {
    setContext({
      currentRequest: undefined,
      searchHistory: [],
      selectedOptions: {
        flights: [],
        hotels: [],
        activities: [],
      },
    });
    setError(null);
    setPendingUpdates(null);
  }, []);

  const saveContext = useCallback(async (): Promise<boolean> => {
    if (!sessionId || !context) return false;

    try {
      const response = await unifiedTravelApi.updateContext(sessionId, context);
      return response.success;
    } catch (err: any) {
      setError(err.message || 'Failed to save context');
      return false;
    }
  }, [sessionId, context]);

  const detectConflicts = useCallback((newData: Partial<TravelRequest>): string[] => {
    const conflicts: string[] = [];
    
    if (!context?.currentRequest) {
      return conflicts;
    }

    const current = context.currentRequest;

    // Check for destination conflicts
    if (newData.destination && current.destination && 
        newData.destination.toLowerCase() !== current.destination.toLowerCase()) {
      conflicts.push(`Destination conflict: "${current.destination}" vs "${newData.destination}"`);
    }

    // Check for date conflicts
    if (newData.departureDate && current.departureDate) {
      const newDate = new Date(newData.departureDate);
      const currentDate = new Date(current.departureDate);
      if (newDate.getTime() !== currentDate.getTime()) {
        conflicts.push(`Departure date conflict: ${current.departureDate} vs ${newData.departureDate}`);
      }
    }

    if (newData.returnDate && current.returnDate) {
      const newDate = new Date(newData.returnDate);
      const currentDate = new Date(current.returnDate);
      if (newDate.getTime() !== currentDate.getTime()) {
        conflicts.push(`Return date conflict: ${current.returnDate} vs ${newData.returnDate}`);
      }
    }

    // Check for traveler count conflicts
    if (newData.travelers !== undefined && current.travelers !== undefined &&
        newData.travelers !== current.travelers) {
      conflicts.push(`Traveler count conflict: ${current.travelers} vs ${newData.travelers}`);
    }

    // Check for budget conflicts
    if (newData.budget !== undefined && current.budget !== undefined &&
        Math.abs(newData.budget - current.budget) > 100) {
      conflicts.push(`Budget conflict: $${current.budget} vs $${newData.budget}`);
    }

    // Store pending updates if conflicts exist
    if (conflicts.length > 0) {
      setPendingUpdates(newData);
    }

    return conflicts;
  }, [context]);

  const resolveConflicts = useCallback((resolution: 'keep_existing' | 'use_new' | 'merge') => {
    if (!pendingUpdates) return;

    switch (resolution) {
      case 'keep_existing':
        // Do nothing, keep current context
        break;
      
      case 'use_new':
        // Replace with new data
        updateCurrentRequest(pendingUpdates);
        break;
      
      case 'merge':
        // Merge data intelligently
        if (context?.currentRequest) {
          const merged: Partial<TravelRequest> = {
            ...context.currentRequest,
            ...pendingUpdates,
            // Special merge logic for certain fields
            travelers: pendingUpdates.travelers || context.currentRequest.travelers,
            budget: pendingUpdates.budget || context.currentRequest.budget,
          };
          updateCurrentRequest(merged);
        }
        break;
    }

    setPendingUpdates(null);
  }, [pendingUpdates, context, updateCurrentRequest]);

  // Auto-save context periodically
  useEffect(() => {
    if (!context || !sessionId) return;

    const saveTimer = setInterval(() => {
      saveContext();
    }, 30000); // Save every 30 seconds

    return () => clearInterval(saveTimer);
  }, [context, sessionId, saveContext]);

  return {
    context,
    isLoading,
    error,
    updateCurrentRequest,
    addToTrip,
    removeFromTrip,
    updateTrip,
    clearContext,
    saveContext,
    detectConflicts,
    resolveConflicts,
  };
};

// Helper function to create a default trip
function createDefaultTrip(request?: TravelRequest): Trip {
  const now = new Date().toISOString();
  return {
    id: `trip_${Date.now()}`,
    name: request?.destination ? `Trip to ${request.destination}` : 'New Trip',
    description: '',
    destination: request?.destination || '',
    startDate: request?.departureDate || '',
    endDate: request?.returnDate || '',
    travelers: [],
    itinerary: [],
    budget: request?.budget,
    status: 'planning',
    createdAt: now,
    updatedAt: now,
  };
}