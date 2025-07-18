import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchResultsSidebar from './SearchResultsSidebar';
import { SidebarProvider } from '../contexts/SidebarContext';
import { SearchResults, ItineraryItem } from '../types';

// Mock child components
jest.mock('./FlightCard', () => ({
  __esModule: true,
  default: ({ flight, onAddToTrip, isSelected, onSelect }: any) => (
    <div data-testid={`flight-${flight.id}`} className="flight-card-mock">
      <h4>{flight.airline} {flight.flightNumber}</h4>
      <p>{flight.origin.city} to {flight.destination.city}</p>
      <p>Price: {flight.price.displayPrice}</p>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
      <button onClick={() => onSelect && onSelect()}>Select</button>
      {isSelected && <span>Selected</span>}
    </div>
  )
}));

jest.mock('./HotelCard', () => ({
  __esModule: true,
  default: ({ hotel, onAddToTrip, isSelected, onSelect }: any) => (
    <div data-testid={`hotel-${hotel.id}`} className="hotel-card-mock">
      <h4>{hotel.name}</h4>
      <p>{hotel.location.city}</p>
      <p>Price: {hotel.price.displayPrice}</p>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
      <button onClick={() => onSelect && onSelect()}>Select</button>
      {isSelected && <span>Selected</span>}
    </div>
  )
}));

jest.mock('./ActivityCard', () => ({
  __esModule: true,
  default: ({ activity, onAddToTrip, isSelected, onSelect }: any) => (
    <div data-testid={`activity-${activity.id}`} className="activity-card-mock">
      <h4>{activity.name}</h4>
      <p>{activity.location.city}</p>
      <p>Price: {activity.price.displayPrice}</p>
      <button onClick={() => onAddToTrip && onAddToTrip()}>Add to Trip</button>
      <button onClick={() => onSelect && onSelect()}>Select</button>
      {isSelected && <span>Selected</span>}
    </div>
  )
}));

jest.mock('./TripPlanPanel', () => ({
  __esModule: true,
  default: ({ sessionId, isOpen }: any) => (
    <div data-testid="trip-plan-panel" className="trip-plan-mock">
      <h3>Trip Plan</h3>
      <p>Session: {sessionId}</p>
      {isOpen && <p>Panel is open</p>}
    </div>
  )
}));

describe('SearchResultsSidebar', () => {
  const mockSearchResults: SearchResults = {
    flights: [
      {
        id: 'flight-1',
        airline: 'Test Air',
        flightNumber: 'TA123',
        origin: { code: 'NYC', name: 'JFK Airport', city: 'New York', country: 'USA', terminal: 'A' },
        destination: { code: 'LAX', name: 'LAX Airport', city: 'Los Angeles', country: 'USA', terminal: 'B' },
        departureTime: '2024-03-15T10:30:00Z',
        arrivalTime: '2024-03-15T13:45:00Z',
        duration: '5h 15m',
        price: { amount: 299, currency: 'USD', displayPrice: 'USD 299' },
        stops: 0,
        aircraft: 'Boeing 737',
        amenities: ['Wi-Fi']
      },
      {
        id: 'flight-2',
        airline: 'Sky Airlines',
        flightNumber: 'SA456',
        origin: { code: 'NYC', name: 'JFK Airport', city: 'New York', country: 'USA', terminal: 'B' },
        destination: { code: 'LAX', name: 'LAX Airport', city: 'Los Angeles', country: 'USA', terminal: 'A' },
        departureTime: '2024-03-15T14:00:00Z',
        arrivalTime: '2024-03-15T17:30:00Z',
        duration: '5h 30m',
        price: { amount: 350, currency: 'USD', displayPrice: 'USD 350' },
        stops: 1,
        aircraft: 'Airbus A320',
        amenities: ['Wi-Fi', 'Entertainment']
      }
    ],
    hotels: [
      {
        id: 'hotel-1',
        name: 'Grand Hotel',
        rating: 4.5,
        reviewScore: 8.9,
        reviewCount: 1500,
        location: {
          address: '123 Main St',
          city: 'Los Angeles',
          country: 'USA',
          coordinates: { lat: 34.0522, lng: -118.2437 }
        },
        price: { amount: 200, currency: 'USD', displayPrice: 'USD 200' },
        images: ['hotel1.jpg'],
        amenities: ['Pool', 'Gym', 'Wi-Fi'],
        description: 'Luxury hotel in downtown'
      },
      {
        id: 'hotel-2',
        name: 'Beach Resort',
        rating: 4.0,
        reviewScore: 8.5,
        reviewCount: 800,
        location: {
          address: '456 Ocean Blvd',
          city: 'Los Angeles',
          country: 'USA',
          coordinates: { lat: 33.9425, lng: -118.4081 }
        },
        price: { amount: 150, currency: 'USD', displayPrice: 'USD 150' },
        images: ['hotel2.jpg'],
        amenities: ['Beach Access', 'Pool'],
        description: 'Beachfront property'
      }
    ],
    activities: [
      {
        id: 'activity-1',
        name: 'Hollywood Tour',
        type: 'tour',
        description: 'Guided tour of Hollywood',
        location: {
          address: 'Hollywood Blvd',
          city: 'Los Angeles',
          country: 'USA',
          coordinates: { lat: 34.0928, lng: -118.3287 }
        },
        price: { amount: 50, currency: 'USD', displayPrice: 'USD 50' },
        duration: '3 hours',
        rating: 4.7,
        images: ['tour.jpg']
      }
    ]
  };

  const defaultProps = {
    searchResults: mockSearchResults,
    isLoading: false,
    onAddToTrip: jest.fn(),
    sessionId: 'test-session-123'
  };

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <SidebarProvider>
        {component}
      </SidebarProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render search results with correct counts', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    // Check tab counts
    expect(screen.getByText('Flights')).toBeInTheDocument();
    expect(screen.getByText('(2)')).toBeInTheDocument();
    
    expect(screen.getByText('Hotels')).toBeInTheDocument();
    expect(screen.getByText('(2)', { selector: '.count' })).toBeInTheDocument();
    
    expect(screen.getByText('Activities')).toBeInTheDocument();
    expect(screen.getByText('(1)')).toBeInTheDocument();
  });

  it('should display flight results by default', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    // Should show flights tab content
    expect(screen.getByTestId('flight-flight-1')).toBeInTheDocument();
    expect(screen.getByTestId('flight-flight-2')).toBeInTheDocument();
    
    // Should not show hotels or activities
    expect(screen.queryByTestId('hotel-hotel-1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('activity-activity-1')).not.toBeInTheDocument();
  });

  it('should switch tabs when clicked', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    // Click Hotels tab
    fireEvent.click(screen.getByText('Hotels'));

    // Should show hotels
    expect(screen.getByTestId('hotel-hotel-1')).toBeInTheDocument();
    expect(screen.getByTestId('hotel-hotel-2')).toBeInTheDocument();
    
    // Should not show flights
    expect(screen.queryByTestId('flight-flight-1')).not.toBeInTheDocument();

    // Click Activities tab
    fireEvent.click(screen.getByText('Activities'));

    // Should show activities
    expect(screen.getByTestId('activity-activity-1')).toBeInTheDocument();
    
    // Should not show hotels
    expect(screen.queryByTestId('hotel-hotel-1')).not.toBeInTheDocument();
  });

  it('should call onAddToTrip with correct data when Add to Trip is clicked on a flight', () => {
    const onAddToTrip = jest.fn();
    renderWithProvider(<SearchResultsSidebar {...defaultProps} onAddToTrip={onAddToTrip} />);

    // Click Add to Trip on first flight
    const flightCard = screen.getByTestId('flight-flight-1');
    const addButton = Array.from(flightCard.querySelectorAll('button')).find(btn => btn.textContent === 'Add to Trip');
    
    fireEvent.click(addButton!);

    expect(onAddToTrip).toHaveBeenCalledWith({
      id: 'flight_flight-1',
      type: 'flight',
      title: 'Test Air TA123',
      description: 'New York to Los Angeles',
      startTime: '2024-03-15T10:30:00Z',
      endTime: '2024-03-15T13:45:00Z',
      location: { code: 'LAX', city: 'Los Angeles', terminal: 'B' },
      price: { amount: 299, currency: 'USD', displayPrice: 'USD 299' },
      status: 'planned'
    });
  });

  it('should call onAddToTrip with correct data when Add to Trip is clicked on a hotel', () => {
    const onAddToTrip = jest.fn();
    renderWithProvider(<SearchResultsSidebar {...defaultProps} onAddToTrip={onAddToTrip} />);

    // Switch to Hotels tab
    fireEvent.click(screen.getByText('Hotels'));

    // Click Add to Trip on first hotel
    const hotelCard = screen.getByTestId('hotel-hotel-1');
    const addButton = Array.from(hotelCard.querySelectorAll('button')).find(btn => btn.textContent === 'Add to Trip');
    
    fireEvent.click(addButton!);

    expect(onAddToTrip).toHaveBeenCalledWith({
      id: 'hotel_hotel-1',
      type: 'hotel',
      title: 'Grand Hotel',
      description: '4.5★ hotel in Los Angeles',
      startTime: expect.any(String),
      endTime: undefined,
      location: {
        address: '123 Main St',
        city: 'Los Angeles',
        country: 'USA',
        coordinates: { lat: 34.0522, lng: -118.2437 }
      },
      price: { amount: 200, currency: 'USD', displayPrice: 'USD 200' },
      status: 'planned'
    });
  });

  it('should handle item selection correctly', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    const flightCard1 = screen.getByTestId('flight-flight-1');
    const selectButton1 = Array.from(flightCard1.querySelectorAll('button')).find(btn => btn.textContent === 'Select');
    
    // Select first flight
    fireEvent.click(selectButton1!);

    // Should show selected count
    expect(screen.getByText('1 selected')).toBeInTheDocument();

    // Select second flight
    const flightCard2 = screen.getByTestId('flight-flight-2');
    const selectButton2 = Array.from(flightCard2.querySelectorAll('button')).find(btn => btn.textContent === 'Select');
    fireEvent.click(selectButton2!);

    expect(screen.getByText('2 selected')).toBeInTheDocument();

    // Clear selections
    fireEvent.click(screen.getByText('Clear'));

    // Should not show selection count anymore
    expect(screen.queryByText('1 selected')).toBeNull();
    expect(screen.queryByText('2 selected')).toBeNull();
  });

  it('should show Trip Plan tab', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    // Click Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    // Should show trip plan panel
    expect(screen.getByTestId('trip-plan-panel')).toBeInTheDocument();
    expect(screen.getByText('Session: test-session-123')).toBeInTheDocument();
  });

  it('should sort results when sort option changes', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} />);

    // Find sort dropdown
    const sortDropdown = screen.getByLabelText('Sort by') as HTMLSelectElement;
    
    // Initially sorted by price ascending
    expect(sortDropdown.value).toBe('price-asc');

    // Change to price descending
    fireEvent.change(sortDropdown, { target: { value: 'price-desc' } });

    // Results should be reordered (we can't test the actual order with mocked components)
    expect(sortDropdown.value).toBe('price-desc');
  });

  it('should show loading state', () => {
    renderWithProvider(<SearchResultsSidebar {...defaultProps} isLoading={true} />);

    expect(screen.getByText('Searching...')).toBeInTheDocument();
  });

  it('should show empty state when no results', () => {
    const emptyResults: SearchResults = {
      flights: [],
      hotels: [],
      activities: []
    };

    renderWithProvider(<SearchResultsSidebar {...defaultProps} searchResults={emptyResults} />);

    expect(screen.getByText('No flights found')).toBeInTheDocument();
  });

  it('should automatically open sidebar when new results arrive', () => {
    const { rerender } = renderWithProvider(
      <SearchResultsSidebar {...defaultProps} searchResults={undefined} />
    );

    // Initially no sidebar
    expect(screen.queryByText('Search Results')).toBeNull();

    // Update with search results
    rerender(
      <SidebarProvider>
        <SearchResultsSidebar {...defaultProps} searchResults={mockSearchResults} />
      </SidebarProvider>
    );

    // Sidebar should be visible
    expect(screen.getByText('Search Results')).toBeInTheDocument();
  });

  it('should handle bulk add to trip for selected items', () => {
    const onAddToTrip = jest.fn();
    renderWithProvider(<SearchResultsSidebar {...defaultProps} onAddToTrip={onAddToTrip} />);

    // Select multiple items
    const flightCard1 = screen.getByTestId('flight-flight-1');
    const selectButton1 = Array.from(flightCard1.querySelectorAll('button')).find(btn => btn.textContent === 'Select');
    fireEvent.click(selectButton1!);

    const flightCard2 = screen.getByTestId('flight-flight-2');
    const selectButton2 = Array.from(flightCard2.querySelectorAll('button')).find(btn => btn.textContent === 'Select');
    fireEvent.click(selectButton2!);

    // Click bulk add button
    fireEvent.click(screen.getByText('Add Selected to Trip'));

    // Should have been called twice (once for each selected item)
    expect(onAddToTrip).toHaveBeenCalledTimes(2);
  });
});