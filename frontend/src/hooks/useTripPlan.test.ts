import { renderHook, act, waitFor } from '@testing-library/react';
import { useTripPlan } from './useTripPlan';
import { unifiedTravelApi } from '../services/unifiedTravelApi';

// Mock the unifiedTravelApi
jest.mock('../services/unifiedTravelApi', () => ({
  unifiedTravelApi: {
    getSession: jest.fn(),
    saveItemToTrip: jest.fn(),
    removeItemFromTrip: jest.fn(),
    exportSessionData: jest.fn()
  }
}));

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn()
  }
});

describe('useTripPlan', () => {
  const mockSessionId = 'test-session-123';
  
  const mockSessionData = {
    success: true,
    data: {
      context: {
        trip: {
          destination: 'Tokyo, Japan',
          departure_date: '2024-07-01',
          return_date: '2024-07-07',
          travelers: 2,
          status: 'draft',
          saved_items: [
            {
              id: 1,
              item_type: 'flight',
              assigned_day: 1,
              user_notes: 'Early morning flight',
              is_booked: true,
              item_data: {
                id: 'flight-1',
                airline: 'JAL',
                flightNumber: 'JL123',
                price: { amount: 1500, currency: 'USD' },
                departureTime: '2024-07-01T06:00:00Z',
                origin: { code: 'LAX', city: 'Los Angeles' },
                destination: { code: 'NRT', city: 'Tokyo' }
              }
            },
            {
              id: 2,
              item_type: 'hotel',
              assigned_day: 1,
              user_notes: 'Near Shibuya station',
              is_booked: false,
              item_data: {
                id: 'hotel-1',
                name: 'Tokyo Grand Hotel',
                price: { amount: 200, currency: 'USD' },
                rating: 4.5,
                location: { city: 'Tokyo' }
              }
            },
            {
              id: 3,
              item_type: 'activity',
              assigned_day: 2,
              user_notes: '',
              is_booked: false,
              item_data: {
                id: 'activity-1',
                name: 'Mt. Fuji Tour',
                price: { amount: 150, currency: 'USD' },
                duration: '1 day',
                rating: 4.8
              }
            }
          ]
        }
      }
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (unifiedTravelApi.getSession as jest.Mock).mockResolvedValue(mockSessionData);
  });

  it('loads trip plan data on mount', async () => {
    const { result } = renderHook(() => useTripPlan(mockSessionId));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(unifiedTravelApi.getSession).toHaveBeenCalledWith(mockSessionId);
    expect(result.current.planSummary).toEqual({
      destination: 'Tokyo, Japan',
      departureDate: '2024-07-01',
      returnDate: '2024-07-07',
      travelers: 2,
      totalCost: {
        amount: 1850,
        currency: 'USD',
        breakdown: {
          flights: 1500,
          hotels: 200,
          activities: 150
        }
      },
      status: 'draft'
    });
  });

  it('organizes items by days correctly', async () => {
    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.planDays).toHaveLength(7); // 7 days trip
    expect(result.current.planDays[0].items).toHaveLength(2); // Flight and hotel on day 1
    expect(result.current.planDays[1].items).toHaveLength(1); // Activity on day 2
    expect(result.current.planDays[0].items[0].type).toBe('flight');
    expect(result.current.planDays[0].items[1].type).toBe('hotel');
  });

  it('handles empty session data gracefully', async () => {
    (unifiedTravelApi.getSession as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        context: {}
      }
    });

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.planSummary).toBeNull();
    expect(result.current.planDays).toEqual([]);
  });

  it('handles API errors', async () => {
    (unifiedTravelApi.getSession as jest.Mock).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load trip plan');
  });

  it('adds item to trip', async () => {
    (unifiedTravelApi.saveItemToTrip as jest.Mock).mockResolvedValue({ success: true });

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newItem = {
      id: 'new-item',
      type: 'activity' as const,
      data: {
        id: 'activity-2',
        name: 'Sushi Making Class',
        price: { amount: 100, currency: 'USD', displayPrice: '$100' },
        type: 'Class',
        description: 'Learn to make sushi',
        location: { address: 'Tokyo', city: 'Tokyo', country: 'Japan' }
      }
    };

    await act(async () => {
      await result.current.addItem(3, newItem);
    });

    expect(unifiedTravelApi.saveItemToTrip).toHaveBeenCalledWith(mockSessionId, {
      id: 'new-item',
      type: 'activity',
      title: 'Sushi Making Class',
      description: '',
      startTime: expect.any(String),
      price: { amount: 100, currency: 'USD', displayPrice: '$100' },
      status: 'planned',
      location: { address: 'Tokyo', city: 'Tokyo', country: 'Japan' }
    });
  });

  it('removes item from trip', async () => {
    (unifiedTravelApi.removeItemFromTrip as jest.Mock).mockResolvedValue({ success: true });

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.removeItem(1, 'item-1');
    });

    expect(unifiedTravelApi.removeItemFromTrip).toHaveBeenCalledWith(mockSessionId, 'item-1');
  });

  it('exports trip plan', async () => {
    const mockExportData = { trip: 'data' };
    (unifiedTravelApi.exportSessionData as jest.Mock).mockResolvedValue({
      success: true,
      data: mockExportData
    });

    // Mock document methods
    const mockLink = {
      href: '',
      download: '',
      click: jest.fn()
    };
    const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
    const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:url');
    const revokeObjectURLSpy = jest.spyOn(URL, 'revokeObjectURL');

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await act(async () => {
      await result.current.exportPlan();
    });

    expect(unifiedTravelApi.exportSessionData).toHaveBeenCalledWith(mockSessionId);
    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(mockLink.download).toBe(`trip-plan-${mockSessionId}.json`);
    expect(mockLink.click).toHaveBeenCalled();

    // Cleanup
    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
  });

  it('shares trip plan and copies to clipboard', async () => {
    const { result } = renderHook(() => useTripPlan(mockSessionId));

    let shareUrl;
    await act(async () => {
      shareUrl = await result.current.sharePlan();
    });

    expect(shareUrl).toBe(`${window.location.origin}/trips/shared/${mockSessionId}`);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(shareUrl);
  });

  it('refreshes trip plan data', async () => {
    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Clear the mock to check it's called again
    (unifiedTravelApi.getSession as jest.Mock).mockClear();

    await act(async () => {
      await result.current.refreshPlan();
    });

    expect(unifiedTravelApi.getSession).toHaveBeenCalledWith(mockSessionId);
  });

  it('does not load when sessionId is not provided', () => {
    const { result } = renderHook(() => useTripPlan(''));

    expect(result.current.isLoading).toBe(false);
    expect(unifiedTravelApi.getSession).not.toHaveBeenCalled();
  });

  it('calculates total cost correctly', async () => {
    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.planSummary?.totalCost).toEqual({
      amount: 1850,
      currency: 'USD',
      breakdown: {
        flights: 1500,
        hotels: 200,
        activities: 150
      }
    });
  });

  it('sorts items by time within each day', async () => {
    const sessionDataWithTimes = {
      ...mockSessionData,
      data: {
        context: {
          trip: {
            ...mockSessionData.data.context.trip,
            saved_items: [
              {
                ...mockSessionData.data.context.trip.saved_items[0],
                item_data: {
                  ...mockSessionData.data.context.trip.saved_items[0].item_data,
                  departureTime: '2024-07-01T14:00:00Z' // 2 PM
                }
              },
              {
                id: 4,
                item_type: 'flight',
                assigned_day: 1,
                item_data: {
                  id: 'flight-2',
                  airline: 'ANA',
                  flightNumber: 'NH456',
                  price: { amount: 1600, currency: 'USD' },
                  departureTime: '2024-07-01T08:00:00Z', // 8 AM
                  origin: { code: 'LAX', city: 'Los Angeles' },
                  destination: { code: 'NRT', city: 'Tokyo' }
                }
              }
            ]
          }
        }
      }
    };

    (unifiedTravelApi.getSession as jest.Mock).mockResolvedValue(sessionDataWithTimes);

    const { result } = renderHook(() => useTripPlan(mockSessionId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should be sorted by time (8 AM flight before 2 PM flight)
    const firstItem = result.current.planDays[0].items[0];
    const secondItem = result.current.planDays[0].items[1];
    
    expect(firstItem.type).toBe('flight');
    expect(secondItem.type).toBe('flight');
    
    if (firstItem.type === 'flight' && 'flightNumber' in firstItem.data) {
      expect(firstItem.data.flightNumber).toBe('NH456');
    }
    
    if (secondItem.type === 'flight' && 'flightNumber' in secondItem.data) {
      expect(secondItem.data.flightNumber).toBe('JL123');
    }
  });
});