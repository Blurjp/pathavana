import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripPlanPanel from './TripPlanPanel';
import { useTripPlan } from '../hooks/useTripPlan';
import { TripPlanSummary, TripPlanDay, TripPlanItem } from '../hooks/useTripPlan';
import { FlightOption, HotelOption, ActivityOption } from '../types';

// Mock the useTripPlan hook
jest.mock('../hooks/useTripPlan');

// Mock config service to prevent API calls
jest.mock('../services/configService', () => ({
  configService: {
    getApiBaseUrl: jest.fn(() => 'http://localhost:8001'),
    getConfig: jest.fn(() => ({
      apiBaseUrl: 'http://localhost:8001',
      oauthRedirectUri: 'http://localhost/auth/callback',
      corsOrigins: ['http://localhost:3000'],
      features: { googleOAuth: false, facebookOAuth: false }
    }))
  }
}));

// Mock API client
jest.mock('../services/api', () => ({
  apiClient: {
    client: {
      defaults: { baseURL: 'http://localhost:8001' }
    },
    updateBaseURL: jest.fn()
  }
}));

const mockUseTripPlan = useTripPlan as jest.MockedFunction<typeof useTripPlan>;

describe('TripPlanPanel', () => {
  const mockAddItem = jest.fn();
  const mockRemoveItem = jest.fn();
  const mockMoveItem = jest.fn();
  const mockUpdateItemNotes = jest.fn();
  const mockReorderItems = jest.fn();
  const mockExportPlan = jest.fn();
  const mockSharePlan = jest.fn();
  const mockRefreshPlan = jest.fn();

  const mockPlanSummary: TripPlanSummary = {
    destination: 'Paris, France',
    departureDate: '2024-06-01',
    returnDate: '2024-06-07',
    travelers: 2,
    totalCost: {
      amount: 3500,
      currency: 'USD',
      breakdown: {
        flights: 1200,
        hotels: 1800,
        activities: 500
      }
    },
    status: 'draft'
  };

  const mockPlanDays: TripPlanDay[] = [
    {
      day: 1,
      date: '2024-06-01',
      items: [
        {
          id: 'flight-1',
          type: 'flight',
          data: {
            id: 'flight-1',
            airline: 'Air France',
            flightNumber: 'AF123',
            origin: { code: 'JFK', name: 'JFK Airport', city: 'New York', country: 'USA' },
            destination: { code: 'CDG', name: 'Charles de Gaulle', city: 'Paris', country: 'France' },
            departureTime: '2024-06-01T10:00:00Z',
            arrivalTime: '2024-06-01T22:00:00Z',
            duration: '7h',
            price: { amount: 600, currency: 'USD', displayPrice: '$600' },
            stops: 0
          } as FlightOption,
          time: '10:00 AM',
          notes: 'Check-in online 24 hours before',
          isBooked: true
        }
      ]
    },
    {
      day: 2,
      date: '2024-06-02',
      items: [
        {
          id: 'hotel-1',
          type: 'hotel',
          data: {
            id: 'hotel-1',
            name: 'Le Marais Hotel',
            rating: 4,
            price: { amount: 300, currency: 'USD', displayPrice: '$300' },
            location: { address: '123 Rue de Rivoli', city: 'Paris', country: 'France' },
            amenities: ['WiFi', 'Breakfast', 'Gym']
          } as HotelOption,
          notes: '',
          isBooked: false
        },
        {
          id: 'activity-1',
          type: 'activity',
          data: {
            id: 'activity-1',
            name: 'Eiffel Tower Tour',
            type: 'Tour',
            description: 'Skip-the-line Eiffel Tower tour',
            price: { amount: 50, currency: 'USD', displayPrice: '$50' },
            location: { address: 'Champ de Mars', city: 'Paris', country: 'France' },
            duration: '2 hours',
            rating: 4.8
          } as ActivityOption,
          notes: '',
          isBooked: false
        }
      ]
    }
  ];

  const defaultMockReturn = {
    planDays: mockPlanDays,
    planSummary: mockPlanSummary,
    isLoading: false,
    error: null,
    addItem: mockAddItem,
    removeItem: mockRemoveItem,
    moveItem: mockMoveItem,
    updateItemNotes: mockUpdateItemNotes,
    reorderItems: mockReorderItems,
    exportPlan: mockExportPlan,
    sharePlan: mockSharePlan,
    refreshPlan: mockRefreshPlan
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTripPlan.mockReturnValue(defaultMockReturn);
  });

  it('renders trip plan panel with summary', () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('Trip Plan')).toBeInTheDocument();
    expect(screen.getByText('Paris, France')).toBeInTheDocument();
    expect(screen.getByText(/Travelers:/)).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Total Cost: $3,500.00')).toBeInTheDocument();
  });

  it('displays cost breakdown correctly', () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('Flights:')).toBeInTheDocument();
    expect(screen.getByText('$1,200.00')).toBeInTheDocument();
    expect(screen.getByText('Hotels:')).toBeInTheDocument();
    expect(screen.getByText('$1,800.00')).toBeInTheDocument();
    expect(screen.getByText('Activities:')).toBeInTheDocument();
    expect(screen.getByText('$500.00')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseTripPlan.mockReturnValue({
      ...defaultMockReturn,
      isLoading: true,
      planDays: [],
      planSummary: null
    });

    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('Loading trip plan...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    mockUseTripPlan.mockReturnValue({
      ...defaultMockReturn,
      error: 'Failed to load trip plan'
    });

    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('Failed to load trip plan')).toBeInTheDocument();
  });

  it('expands and collapses day sections', () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    // Find day headers by text that includes "Day 1" and "Day 2"
    const day1Header = screen.getByText((content, element) => {
      return element?.tagName === 'H5' && content.includes('Day 1');
    });
    const day2Header = screen.getByText((content, element) => {
      return element?.tagName === 'H5' && content.includes('Day 2');
    });

    // Day 1 should be expanded by default
    expect(screen.getByText('Air France AF123')).toBeInTheDocument();

    // Click to collapse day 1
    fireEvent.click(day1Header);
    expect(screen.queryByText('Air France AF123')).toBeNull();

    // Click to expand day 2
    fireEvent.click(day2Header);
    expect(screen.getByText('Le Marais Hotel')).toBeInTheDocument();
  });

  it('displays flight details correctly', () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('JFK')).toBeInTheDocument();
    expect(screen.getByText('CDG')).toBeInTheDocument();
    expect(screen.getByText('Air France AF123')).toBeInTheDocument();
    expect(screen.getByText('7h')).toBeInTheDocument();
    expect(screen.getByText('$600.00')).toBeInTheDocument();
    expect(screen.getByText('Booked')).toBeInTheDocument();
  });

  it('allows editing notes', async () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    // Find and click edit notes button
    const editButtons = screen.getAllByText('Edit notes');
    fireEvent.click(editButtons[0]);

    // Find textarea and update notes
    const textarea = screen.getByPlaceholderText('Add notes...');
    fireEvent.change(textarea, { target: { value: 'Updated notes' } });

    // Save notes
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateItemNotes).toHaveBeenCalledWith(1, 'flight-1', 'Updated notes');
    });
  });

  it('handles item removal', async () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    // Expand day 2 to see items
    const day2Header = screen.getByText((content, element) => {
      return element?.tagName === 'H5' && content.includes('Day 2');
    });
    fireEvent.click(day2Header);

    // Find and click remove button (🗑️ emoji)
    const removeButtons = screen.getAllByTitle('Remove from trip');
    fireEvent.click(removeButtons[1]); // Remove hotel item

    await waitFor(() => {
      expect(mockRemoveItem).toHaveBeenCalledWith(2, 'hotel-1');
    });
  });

  it('handles export functionality', async () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    const exportButton = screen.getByTitle('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockExportPlan).toHaveBeenCalled();
    });
  });

  it('handles share functionality with success message', async () => {
    mockSharePlan.mockResolvedValue('https://example.com/trips/shared/test-session');

    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    const shareButton = screen.getByTitle('Share');
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(mockSharePlan).toHaveBeenCalled();
    });

    // The success message appears after the promise resolves
    await waitFor(() => {
      expect(screen.getByText('Link copied to clipboard! 📋')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles refresh functionality', async () => {
    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    const refreshButton = screen.getByTitle('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockRefreshPlan).toHaveBeenCalled();
    });
  });

  it('renders empty state when no plan exists', () => {
    mockUseTripPlan.mockReturnValue({
      ...defaultMockReturn,
      planDays: [],
      planSummary: null
    });

    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('No trip plan yet. Start adding items to create your itinerary!')).toBeInTheDocument();
  });

  it('renders empty day message', () => {
    mockUseTripPlan.mockReturnValue({
      ...defaultMockReturn,
      planDays: [{
        day: 1,
        date: '2024-06-01',
        items: []
      }]
    });

    render(<TripPlanPanel sessionId="test-session" isOpen={true} />);

    expect(screen.getByText('No items planned for this day')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(<TripPlanPanel sessionId="test-session" isOpen={false} />);

    expect(container.firstChild).toBeNull();
  });

  it('handles close button when onClose is provided', () => {
    const mockOnClose = jest.fn();
    render(<TripPlanPanel sessionId="test-session" isOpen={true} onClose={mockOnClose} />);

    const closeButton = screen.getByTitle('Close');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });
});