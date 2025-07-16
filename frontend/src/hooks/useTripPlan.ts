import { useState, useEffect, useCallback } from 'react';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { FlightOption, HotelOption, ActivityOption } from '../types';

export interface TripPlanDay {
  day: number;
  date: string;
  items: TripPlanItem[];
}

export interface TripPlanItem {
  id: string;
  type: 'flight' | 'hotel' | 'activity' | 'transport' | 'meal' | 'note';
  data: FlightOption | HotelOption | ActivityOption | { content: string };
  time?: string;
  duration?: number; // in minutes
  notes?: string;
  isBooked?: boolean;
}

export interface TripPlanSummary {
  destination: string;
  departureDate: string;
  returnDate: string;
  travelers: number;
  totalCost: {
    amount: number;
    currency: string;
    breakdown: {
      flights: number;
      hotels: number;
      activities: number;
    };
  };
  status: 'draft' | 'confirmed' | 'booked';
}

interface UseTripPlanReturn {
  planDays: TripPlanDay[];
  planSummary: TripPlanSummary | null;
  isLoading: boolean;
  error: string | null;
  addItem: (day: number, item: TripPlanItem) => Promise<void>;
  removeItem: (day: number, itemId: string) => Promise<void>;
  moveItem: (fromDay: number, toDay: number, itemId: string) => Promise<void>;
  updateItemNotes: (day: number, itemId: string, notes: string) => Promise<void>;
  reorderItems: (day: number, itemIds: string[]) => Promise<void>;
  exportPlan: () => Promise<void>;
  sharePlan: () => Promise<string>;
  refreshPlan: () => Promise<void>;
}

export const useTripPlan = (sessionId: string): UseTripPlanReturn => {
  const [planDays, setPlanDays] = useState<TripPlanDay[]>([]);
  const [planSummary, setPlanSummary] = useState<TripPlanSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load trip plan data from session
  const loadTripPlan = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      // Get session data including plan_data
      const sessionResponse = await unifiedTravelApi.getSession(sessionId);
      
      if (sessionResponse.success && sessionResponse.data) {
        const session = sessionResponse.data;
        const planData = session.context?.trip as any; // Use any to handle different data structures
        
        if (planData) {
          // Extract summary information
          const summary: TripPlanSummary = {
            destination: planData.destination || 'Unknown',
            departureDate: planData.departure_date || planData.startDate || '',
            returnDate: planData.return_date || planData.endDate || '',
            travelers: planData.travelers || 1,
            totalCost: calculateTotalCost(planData),
            status: planData.status || 'draft'
          };
          setPlanSummary(summary);

          // Organize items by day
          const days = organizePlanByDays(planData, summary.departureDate, summary.returnDate);
          setPlanDays(days);
        }
      }
    } catch (err) {
      console.error('Failed to load trip plan:', err);
      setError('Failed to load trip plan');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Calculate total cost from plan data
  const calculateTotalCost = (planData: any) => {
    const breakdown = {
      flights: 0,
      hotels: 0,
      activities: 0
    };

    // Sum up costs from saved items
    if (planData.saved_items) {
      planData.saved_items.forEach((item: any) => {
        const price = item.item_data?.price?.amount || 0;
        switch (item.item_type) {
          case 'flight':
            breakdown.flights += price;
            break;
          case 'hotel':
            breakdown.hotels += price;
            break;
          case 'activity':
            breakdown.activities += price;
            break;
        }
      });
    }

    return {
      amount: breakdown.flights + breakdown.hotels + breakdown.activities,
      currency: 'USD',
      breakdown
    };
  };

  // Organize plan items by days
  const organizePlanByDays = (planData: any, departureDate: string, returnDate: string): TripPlanDay[] => {
    if (!departureDate || !returnDate) return [];

    const start = new Date(departureDate);
    const end = new Date(returnDate);
    const dayCount = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    const days: TripPlanDay[] = [];
    
    for (let i = 0; i < dayCount; i++) {
      const date = new Date(start);
      date.setDate(date.getDate() + i);
      
      days.push({
        day: i + 1,
        date: date.toISOString().split('T')[0],
        items: []
      });
    }

    // Add saved items to appropriate days
    if (planData.saved_items) {
      planData.saved_items.forEach((savedItem: any) => {
        const dayIndex = (savedItem.assigned_day || 1) - 1;
        if (dayIndex >= 0 && dayIndex < days.length) {
          const planItem: TripPlanItem = {
            id: savedItem.id?.toString() || `temp_${Date.now()}`,
            type: savedItem.item_type,
            data: savedItem.item_data,
            notes: savedItem.user_notes,
            isBooked: savedItem.is_booked
          };

          // Extract time from item data if available
          if (savedItem.item_type === 'flight' && savedItem.item_data.departureTime) {
            planItem.time = new Date(savedItem.item_data.departureTime).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit'
            });
          }

          days[dayIndex].items.push(planItem);
        }
      });

      // Sort items within each day by time if available
      days.forEach(day => {
        day.items.sort((a, b) => {
          if (a.time && b.time) {
            return a.time.localeCompare(b.time);
          }
          return 0;
        });
      });
    }

    return days;
  };

  // Add item to a specific day
  const addItem = useCallback(async (day: number, item: TripPlanItem) => {
    try {
      // Only save items that are valid ItineraryItem types
      if (item.type === 'note') {
        // For notes, we might want to save them differently or skip for now
        console.warn('Note items are not supported as itinerary items yet');
        return;
      }
      
      const response = await unifiedTravelApi.saveItemToTrip(sessionId, {
        id: item.id,
        type: item.type as 'flight' | 'hotel' | 'activity' | 'transport' | 'meal',
        title: getItemTitle(item),
        description: item.notes || '',
        startTime: new Date().toISOString(),
        price: getItemPrice(item),
        status: 'planned',
        location: getItemLocation(item)
      });

      if (response.success) {
        await refreshPlan();
      }
    } catch (err) {
      console.error('Failed to add item to trip:', err);
      setError('Failed to add item to trip');
    }
  }, [sessionId]);

  // Helper functions to extract data from items
  const getItemTitle = (item: TripPlanItem): string => {
    if (item.type === 'flight') {
      const flight = item.data as FlightOption;
      return `${flight.airline} ${flight.flightNumber}`;
    } else if (item.type === 'hotel') {
      const hotel = item.data as HotelOption;
      return hotel.name;
    } else if (item.type === 'activity') {
      const activity = item.data as ActivityOption;
      return activity.name;
    } else {
      const note = item.data as { content: string };
      return note.content;
    }
  };

  const getItemPrice = (item: TripPlanItem): any => {
    if (item.type === 'note') {
      return { amount: 0, currency: 'USD' };
    }
    const data = item.data as FlightOption | HotelOption | ActivityOption;
    return data.price;
  };

  const getItemLocation = (item: TripPlanItem): any => {
    if (item.type === 'flight') {
      const flight = item.data as FlightOption;
      return flight.destination;
    } else if (item.type === 'hotel' || item.type === 'activity') {
      const data = item.data as HotelOption | ActivityOption;
      return data.location;
    }
    return null;
  };

  // Remove item from a day
  const removeItem = useCallback(async (day: number, itemId: string) => {
    try {
      await unifiedTravelApi.removeItemFromTrip(sessionId, itemId);
      await refreshPlan();
    } catch (err) {
      console.error('Failed to remove item:', err);
      setError('Failed to remove item');
    }
  }, [sessionId]);

  // Move item between days
  const moveItem = useCallback(async (fromDay: number, toDay: number, itemId: string) => {
    // TODO: Implement API endpoint to update item's assigned_day
    console.log('Moving item', itemId, 'from day', fromDay, 'to day', toDay);
    await refreshPlan();
  }, [sessionId]);

  // Update item notes
  const updateItemNotes = useCallback(async (day: number, itemId: string, notes: string) => {
    // TODO: Implement API endpoint to update item notes
    console.log('Updating notes for item', itemId, 'to', notes);
    await refreshPlan();
  }, [sessionId]);

  // Reorder items within a day
  const reorderItems = useCallback(async (day: number, itemIds: string[]) => {
    // TODO: Implement API endpoint to update item sort_order
    console.log('Reordering items in day', day, 'to', itemIds);
    await refreshPlan();
  }, [sessionId]);

  // Export trip plan
  const exportPlan = useCallback(async () => {
    try {
      const response = await unifiedTravelApi.exportSessionData(sessionId);
      if (response.success && response.data) {
        // Create and download file
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trip-plan-${sessionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to export plan:', err);
      setError('Failed to export plan');
    }
  }, [sessionId]);

  // Share trip plan
  const sharePlan = useCallback(async (): Promise<string> => {
    // Generate shareable link
    const shareUrl = `${window.location.origin}/trips/shared/${sessionId}`;
    
    // Copy to clipboard
    try {
      await navigator.clipboard.writeText(shareUrl);
      return shareUrl;
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      throw err;
    }
  }, [sessionId]);

  // Refresh plan data
  const refreshPlan = useCallback(async () => {
    await loadTripPlan();
  }, [loadTripPlan]);

  // Load trip plan on mount and when sessionId changes
  useEffect(() => {
    loadTripPlan();
  }, [loadTripPlan]);

  return {
    planDays,
    planSummary,
    isLoading,
    error,
    addItem,
    removeItem,
    moveItem,
    updateItemNotes,
    reorderItems,
    exportPlan,
    sharePlan,
    refreshPlan
  };
};