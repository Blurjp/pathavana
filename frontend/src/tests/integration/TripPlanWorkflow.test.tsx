import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SidebarProvider } from '../../contexts/SidebarContext';
import SearchResultsSidebar from '../../components/SearchResultsSidebar';
import TripPlanPanel from '../../components/TripPlanPanel';
import { useTripPlan } from '../../hooks/useTripPlan';
import { SearchResults, ItineraryItem } from '../../types';

// Mock the useTripPlan hook
jest.mock('../../hooks/useTripPlan');

// Mock config service to prevent network calls
jest.mock('../../services/configService', () => ({
  configService: {
    getApiBaseUrl: jest.fn().mockResolvedValue('http://localhost:8001'),
    getConfig: jest.fn().mockResolvedValue({
      apiBaseUrl: 'http://localhost:8001',
      features: {}
    })
  }
}));

// Mock child components to simplify testing
jest.mock('../../components/FlightCard', () => ({
  __esModule: true,
  default: ({ flight, onAddToTrip }: any) => (
    <div data-testid={`flight-${flight.id}`}>
      <h4>{flight.airline} {flight.flightNumber}</h4>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
    </div>
  )
}));

jest.mock('../../components/HotelCard', () => ({
  __esModule: true,
  default: ({ hotel, onAddToTrip }: any) => (
    <div data-testid={`hotel-${hotel.id}`}>
      <h4>{hotel.name}</h4>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
    </div>
  )
}));

jest.mock('../../components/ActivityCard', () => ({
  __esModule: true,
  default: ({ activity, onAddToTrip }: any) => (
    <div data-testid={`activity-${activity.id}`}>
      <h4>{activity.name}</h4>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
    </div>
  )
}));

describe('Trip Plan Workflow Integration', () => {
  const mockSearchResults: SearchResults = {
    flights: [
      {
        id: 'flight-1',
        airline: 'Delta Airlines',
        flightNumber: 'DL100',
        origin: { code: 'NYC', name: 'New York City Airport', city: 'New York', country: 'USA' },
        destination: { code: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'USA' },
        departureTime: '2024-05-01T09:00:00',
        arrivalTime: '2024-05-01T12:00:00',
        duration: '6h',
        price: { amount: 350, currency: 'USD', displayPrice: 'USD 350' },
        stops: 0
      }
    ],
    hotels: [
      {
        id: 'hotel-1',
        name: 'Beverly Hills Hotel',
        rating: 5,
        location: { address: '123 Sunset Blvd', city: 'Beverly Hills', country: 'USA' },
        price: { amount: 400, currency: 'USD', displayPrice: 'USD 400' },
        amenities: ['Pool', 'Spa', 'Restaurant'],
        images: ['hotel.jpg']
      }
    ],
    activities: [
      {
        id: 'activity-1',
        name: 'Hollywood Tour',
        type: 'tour',
        description: 'Guided tour of Hollywood',
        location: { address: 'Hollywood Blvd', city: 'Los Angeles', country: 'USA' },
        price: { amount: 75, currency: 'USD', displayPrice: 'USD 75' },
        duration: '3 hours',
        rating: 4.5
      }
    ]
  };

  let mockTripPlanData: any;
  let mockAddItem: jest.Mock;
  let mockRemoveItem: jest.Mock;
  let mockUpdateItemNotes: jest.Mock;

  beforeEach(() => {
    // Initialize mock trip plan data
    mockTripPlanData = {
      planDays: [
        { day: 1, date: '2024-05-01', items: [] },
        { day: 2, date: '2024-05-02', items: [] },
        { day: 3, date: '2024-05-03', items: [] }
      ],
      planSummary: {
        destination: 'Los Angeles',
        departureDate: '2024-05-01',
        returnDate: '2024-05-03',
        travelers: 2,
        totalCost: {
          amount: 0,
          currency: 'USD',
          breakdown: { flights: 0, hotels: 0, activities: 0 }
        },
        status: 'draft'
      },
      isLoading: false,
      error: null
    };

    mockAddItem = jest.fn(async (day: number, item: any) => {
      const dayIndex = mockTripPlanData.planDays.findIndex((d: any) => d.day === day);
      if (dayIndex !== -1) {
        mockTripPlanData.planDays[dayIndex].items.push(item);
        
        // Update costs
        if (item.type === 'flight') {
          mockTripPlanData.planSummary.totalCost.breakdown.flights += item.data.price.amount;
        } else if (item.type === 'hotel') {
          mockTripPlanData.planSummary.totalCost.breakdown.hotels += item.data.price.amount;
        } else if (item.type === 'activity') {
          mockTripPlanData.planSummary.totalCost.breakdown.activities += item.data.price.amount;
        }
        
        mockTripPlanData.planSummary.totalCost.amount = 
          mockTripPlanData.planSummary.totalCost.breakdown.flights +
          mockTripPlanData.planSummary.totalCost.breakdown.hotels +
          mockTripPlanData.planSummary.totalCost.breakdown.activities;
      }
    });

    mockRemoveItem = jest.fn(async (day: number, itemId: string) => {
      const dayIndex = mockTripPlanData.planDays.findIndex((d: any) => d.day === day);
      if (dayIndex !== -1) {
        const itemIndex = mockTripPlanData.planDays[dayIndex].items.findIndex((item: any) => item.id === itemId);
        if (itemIndex !== -1) {
          const removedItem = mockTripPlanData.planDays[dayIndex].items[itemIndex];
          mockTripPlanData.planDays[dayIndex].items.splice(itemIndex, 1);
          
          // Update costs
          if (removedItem.type === 'flight') {
            mockTripPlanData.planSummary.totalCost.breakdown.flights -= removedItem.data.price.amount;
          } else if (removedItem.type === 'hotel') {
            mockTripPlanData.planSummary.totalCost.breakdown.hotels -= removedItem.data.price.amount;
          } else if (removedItem.type === 'activity') {
            mockTripPlanData.planSummary.totalCost.breakdown.activities -= removedItem.data.price.amount;
          }
          
          mockTripPlanData.planSummary.totalCost.amount = 
            mockTripPlanData.planSummary.totalCost.breakdown.flights +
            mockTripPlanData.planSummary.totalCost.breakdown.hotels +
            mockTripPlanData.planSummary.totalCost.breakdown.activities;
        }
      }
    });

    mockUpdateItemNotes = jest.fn(async (day: number, itemId: string, notes: string) => {
      const dayIndex = mockTripPlanData.planDays.findIndex((d: any) => d.day === day);
      if (dayIndex !== -1) {
        const item = mockTripPlanData.planDays[dayIndex].items.find((item: any) => item.id === itemId);
        if (item) {
          item.notes = notes;
        }
      }
    });

    // Mock useTripPlan
    (useTripPlan as jest.MockedFunction<typeof useTripPlan>).mockReturnValue({
      ...mockTripPlanData,
      addItem: mockAddItem,
      removeItem: mockRemoveItem,
      moveItem: jest.fn(),
      updateItemNotes: mockUpdateItemNotes,
      reorderItems: jest.fn(),
      exportPlan: jest.fn(),
      sharePlan: jest.fn(),
      refreshPlan: jest.fn()
    });
  });

  const renderComponents = () => {
    const handleAddToTrip = (item: ItineraryItem) => {
      // Simulate adding to day 1 for simplicity
      let itemData: any;
      
      if (item.type === 'flight') {
        itemData = mockSearchResults.flights?.find(
          f => f.id === item.id.replace('flight_', '')
        );
      } else if (item.type === 'hotel') {
        itemData = mockSearchResults.hotels?.find(
          h => h.id === item.id.replace('hotel_', '')
        );
      } else if (item.type === 'activity') {
        itemData = mockSearchResults.activities?.find(
          a => a.id === item.id.replace('activity_', '')
        );
      }
      
      mockAddItem(1, {
        id: item.id,
        type: item.type,
        data: itemData,
        time: new Date().toISOString(),
        notes: '',
        isBooked: false
      });
    };

    return render(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={handleAddToTrip}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );
  };

  it('should add flight to trip plan and show in panel', async () => {
    const { rerender } = renderComponents();

    // Verify flight is displayed in search results
    expect(screen.getByText('Delta Airlines DL100')).toBeInTheDocument();

    // Add flight to trip
    const addFlightButton = within(screen.getByTestId('flight-flight-1')).getByText('Add to Trip');
    fireEvent.click(addFlightButton);

    // Wait for the item to be added
    await waitFor(() => {
      expect(mockAddItem).toHaveBeenCalledWith(1, expect.objectContaining({
        id: 'flight_flight-1',
        type: 'flight'
      }));
    });

    // Re-render to see updated trip plan
    rerender(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={jest.fn()}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );

    // Verify flight appears in trip plan
    const tripPlanSection = screen.getByTestId('trip-plan-days');
    expect(within(tripPlanSection).getByText('Delta Airlines DL100')).toBeInTheDocument();
    expect(within(tripPlanSection).getByText('$350.00')).toBeInTheDocument();
  });

  it('should handle complete trip planning flow', async () => {
    const { rerender } = renderComponents();

    // Add flight
    fireEvent.click(within(screen.getByTestId('flight-flight-1')).getByText('Add to Trip'));

    // Switch to hotels tab
    fireEvent.click(screen.getByText('Hotels'));

    // Add hotel
    fireEvent.click(within(screen.getByTestId('hotel-hotel-1')).getByText('Add to Trip'));

    // Switch to activities tab
    fireEvent.click(screen.getByText('Activities'));

    // Add activity
    fireEvent.click(within(screen.getByTestId('activity-activity-1')).getByText('Add to Trip'));

    // Wait for all items to be added
    await waitFor(() => {
      expect(mockAddItem).toHaveBeenCalledTimes(3);
    });

    // Re-render to see updated trip plan
    rerender(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={jest.fn()}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );

    // Switch to Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    // Verify all items are in trip plan
    expect(screen.getByText('Total Cost: $825.00')).toBeInTheDocument();
    expect(screen.getByText('Flights:')).toBeInTheDocument();
    expect(screen.getByText('$350.00')).toBeInTheDocument();
    expect(screen.getByText('Hotels:')).toBeInTheDocument();
    expect(screen.getByText('$400.00')).toBeInTheDocument();
    expect(screen.getByText('Activities:')).toBeInTheDocument();
    expect(screen.getByText('$75.00')).toBeInTheDocument();
  });

  it('should update notes on trip plan items', async () => {
    // First add an item
    const { rerender } = renderComponents();
    fireEvent.click(within(screen.getByTestId('flight-flight-1')).getByText('Add to Trip'));

    await waitFor(() => {
      expect(mockAddItem).toHaveBeenCalled();
    });

    // Re-render to see the item in trip plan
    rerender(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={jest.fn()}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );

    // Switch to Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    // Edit notes
    const editButton = screen.getByText('Edit notes');
    fireEvent.click(editButton);

    const textarea = screen.getByPlaceholderText('Add notes...');
    fireEvent.change(textarea, { target: { value: 'Remember to check in online' } });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateItemNotes).toHaveBeenCalledWith(1, 'flight_flight-1', 'Remember to check in online');
    });
  });

  it('should remove items from trip plan', async () => {
    // First add items
    const { rerender } = renderComponents();
    fireEvent.click(within(screen.getByTestId('flight-flight-1')).getByText('Add to Trip'));
    fireEvent.click(screen.getByText('Hotels'));
    fireEvent.click(within(screen.getByTestId('hotel-hotel-1')).getByText('Add to Trip'));

    await waitFor(() => {
      expect(mockAddItem).toHaveBeenCalledTimes(2);
    });

    // Re-render to see items in trip plan
    rerender(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={jest.fn()}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );

    // Switch to Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    // Verify total before removal
    expect(screen.getByText('Total Cost: $750.00')).toBeInTheDocument();

    // Remove flight
    const removeButtons = screen.getAllByTitle('Remove from trip');
    fireEvent.click(removeButtons[0]);

    await waitFor(() => {
      expect(mockRemoveItem).toHaveBeenCalledWith(1, 'flight_flight-1');
    });

    // Re-render to see updated trip plan
    rerender(
      <SidebarProvider>
        <div style={{ display: 'flex' }}>
          <SearchResultsSidebar
            searchResults={mockSearchResults}
            isLoading={false}
            onAddToTrip={jest.fn()}
            sessionId="test-session"
          />
          <TripPlanPanel
            sessionId="test-session"
            isOpen={true}
          />
        </div>
      </SidebarProvider>
    );

    // Verify updated total
    expect(screen.getByText('Total Cost: $400.00')).toBeInTheDocument();
  });

  it('should show empty state when no items in trip plan', () => {
    renderComponents();

    // Switch to Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    expect(screen.getByText('No trip plan yet. Start adding items to create your itinerary!')).toBeInTheDocument();
  });

  it('should switch between search tabs seamlessly', async () => {
    renderComponents();

    // Initially shows flights
    expect(screen.getByText('Delta Airlines DL100')).toBeInTheDocument();

    // Switch to hotels
    fireEvent.click(screen.getByText('Hotels'));
    expect(screen.getByText('Beverly Hills Hotel')).toBeInTheDocument();

    // Switch to activities
    fireEvent.click(screen.getByText('Activities'));
    expect(screen.getByText('Hollywood Tour')).toBeInTheDocument();

    // Switch back to flights
    fireEvent.click(screen.getByText('Flights'));
    expect(screen.getByText('Delta Airlines DL100')).toBeInTheDocument();
  });
});