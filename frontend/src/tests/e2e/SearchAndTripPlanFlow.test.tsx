import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UnifiedTravelRequest from '../../pages/UnifiedTravelRequest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { SidebarProvider } from '../../contexts/SidebarContext';

// Mock the API calls
jest.mock('../../services/unifiedTravelApi', () => ({
  unifiedTravelApi: {
    searchTravel: jest.fn().mockResolvedValue({
      success: true,
      data: {
        flights: [
          {
            id: 'flight-1',
            airline: 'American Airlines',
            flightNumber: 'AA100',
            origin: { code: 'JFK', name: 'John F. Kennedy International Airport', city: 'New York', country: 'USA', terminal: '8' },
            destination: { code: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'USA', terminal: '4' },
            departureTime: '2024-05-01T09:00:00Z',
            arrivalTime: '2024-05-01T12:30:00Z',
            duration: '5h 30m',
            price: { amount: 450, currency: 'USD', displayPrice: 'USD 450' },
            stops: 0,
            aircraft: 'Boeing 777',
            amenities: ['Wi-Fi', 'Entertainment', 'Power outlets']
          }
        ],
        hotels: [
          {
            id: 'hotel-1',
            name: 'Sunset Boulevard Hotel',
            rating: 4.5,
            reviewScore: 8.8,
            reviewCount: 1200,
            location: {
              address: '8820 Sunset Blvd',
              city: 'West Hollywood',
              country: 'USA',
              coordinates: { lat: 34.0900, lng: -118.3867 }
            },
            price: { amount: 280, currency: 'USD', displayPrice: 'USD 280' },
            images: ['hotel1.jpg'],
            amenities: ['Pool', 'Gym', 'Restaurant', 'Bar'],
            description: 'Modern hotel on the famous Sunset Boulevard'
          }
        ],
        activities: []
      }
    }),
    createSession: jest.fn().mockResolvedValue({
      success: true,
      data: { session_id: 'test-session-123' }
    }),
    getSession: jest.fn().mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session-123',
        context: {
          trip: {
            destination: 'Los Angeles',
            departure_date: '2024-05-01',
            return_date: '2024-05-03',
            travelers: 1
          }
        }
      }
    }),
    updateSession: jest.fn().mockResolvedValue({ success: true })
  }
}));

// Mock ConversationalSearch service
jest.mock('../../services/ConversationalSearch', () => ({
  ConversationalSearch: {
    sendMessage: jest.fn().mockResolvedValue({
      response: 'I found great flights and hotels for your Los Angeles trip!',
      searchResults: {
        flights: [
          {
            id: 'flight-1',
            airline: 'American Airlines',
            flightNumber: 'AA100',
            origin: { code: 'JFK', name: 'John F. Kennedy International Airport', city: 'New York', country: 'USA', terminal: '8' },
            destination: { code: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'USA', terminal: '4' },
            departureTime: '2024-05-01T09:00:00Z',
            arrivalTime: '2024-05-01T12:30:00Z',
            duration: '5h 30m',
            price: { amount: 450, currency: 'USD', displayPrice: 'USD 450' },
            stops: 0,
            aircraft: 'Boeing 777',
            amenities: ['Wi-Fi', 'Entertainment', 'Power outlets']
          }
        ],
        hotels: [
          {
            id: 'hotel-1',
            name: 'Sunset Boulevard Hotel',
            rating: 4.5,
            reviewScore: 8.8,
            reviewCount: 1200,
            location: {
              address: '8820 Sunset Blvd',
              city: 'West Hollywood',
              country: 'USA',
              coordinates: { lat: 34.0900, lng: -118.3867 }
            },
            price: { amount: 280, currency: 'USD', displayPrice: 'USD 280' },
            images: ['hotel1.jpg'],
            amenities: ['Pool', 'Gym', 'Restaurant', 'Bar'],
            description: 'Modern hotel on the famous Sunset Boulevard'
          }
        ],
        activities: []
      }
    })
  }
}));

describe('Search and Trip Plan Flow E2E', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User'
  };

  const renderApp = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <SidebarProvider>
            <UnifiedTravelRequest />
          </SidebarProvider>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Clear localStorage
    window.localStorage.clear();
  });

  it('should search for flights and hotels and add them to trip plan', async () => {
    renderApp();

    // Wait for the component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/where would you like to travel/i)).toBeInTheDocument();
    });

    // Type a search query
    const input = screen.getByPlaceholderText(/where would you like to travel/i);
    fireEvent.change(input, { 
      target: { value: 'Find me flights and hotels for Los Angeles from May 1-3' } 
    });

    // Submit the search
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    // Wait for search results to appear
    await waitFor(() => {
      expect(screen.getByText('Search Results')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Verify flight results are shown
    expect(screen.getByText('American Airlines AA100')).toBeInTheDocument();
    expect(screen.getByText('New York to Los Angeles')).toBeInTheDocument();
    expect(screen.getByText('USD 450')).toBeInTheDocument();

    // Switch to Hotels tab
    fireEvent.click(screen.getByText('Hotels'));

    // Verify hotel results are shown
    await waitFor(() => {
      expect(screen.getByText('Sunset Boulevard Hotel')).toBeInTheDocument();
      expect(screen.getByText('West Hollywood')).toBeInTheDocument();
      expect(screen.getByText('USD 280')).toBeInTheDocument();
    });

    // Add flight to trip
    fireEvent.click(screen.getByText('Flights'));
    const addFlightButton = screen.getAllByText('Add to Trip')[0];
    fireEvent.click(addFlightButton);

    // Switch to Trip Plan tab
    fireEvent.click(screen.getByText('Trip Plan'));

    // Verify flight appears in trip plan
    await waitFor(() => {
      expect(screen.getByTestId('trip-plan-panel')).toBeInTheDocument();
      expect(screen.getByText('American Airlines AA100')).toBeInTheDocument();
    });

    // Go back and add hotel
    fireEvent.click(screen.getByText('Hotels'));
    const addHotelButton = screen.getAllByText('Add to Trip')[0];
    fireEvent.click(addHotelButton);

    // Switch back to Trip Plan
    fireEvent.click(screen.getByText('Trip Plan'));

    // Verify both items are in trip plan
    await waitFor(() => {
      const tripPanel = screen.getByTestId('trip-plan-panel');
      expect(tripPanel).toHaveTextContent('American Airlines AA100');
      expect(tripPanel).toHaveTextContent('Sunset Boulevard Hotel');
    });
  });

  it('should handle removing items from trip plan', async () => {
    renderApp();

    // Setup: Add items to trip first
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/where would you like to travel/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/where would you like to travel/i);
    fireEvent.change(input, { 
      target: { value: 'Find flights to LA' } 
    });

    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Search Results')).toBeInTheDocument();
    });

    // Add flight
    const addFlightButton = screen.getAllByText('Add to Trip')[0];
    fireEvent.click(addFlightButton);

    // Go to Trip Plan
    fireEvent.click(screen.getByText('Trip Plan'));

    await waitFor(() => {
      expect(screen.getByText('American Airlines AA100')).toBeInTheDocument();
    });

    // Find and click remove button
    const removeButton = screen.getByTestId('remove-flight_flight-1');
    fireEvent.click(removeButton);

    // Verify item is removed
    await waitFor(() => {
      expect(screen.queryByText('American Airlines AA100')).not.toBeInTheDocument();
    });
  });

  it('should update trip plan costs when adding multiple items', async () => {
    renderApp();

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything about your travel plans/i)).toBeInTheDocument();
    });

    // Search for travel options
    const input = screen.getByPlaceholderText(/ask me anything about your travel plans/i);
    fireEvent.change(input, { 
      target: { value: 'Find flights and hotels for LA' } 
    });

    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Search Results')).toBeInTheDocument();
    });

    // Add flight (450 USD)
    const addFlightButton = screen.getAllByText('Add to Trip')[0];
    fireEvent.click(addFlightButton);

    // Add hotel (280 USD)
    fireEvent.click(screen.getByText('Hotels'));
    const addHotelButton = screen.getAllByText('Add to Trip')[0];
    fireEvent.click(addHotelButton);

    // Go to Trip Plan
    fireEvent.click(screen.getByText('Trip Plan'));

    // Verify total cost is updated (450 + 280 = 730)
    await waitFor(() => {
      const tripPanel = screen.getByTestId('trip-plan-panel');
      expect(tripPanel).toHaveTextContent('Total Cost: USD 730');
      expect(tripPanel).toHaveTextContent('Flights: 450');
      expect(tripPanel).toHaveTextContent('Hotels: 280');
    });
  });
});