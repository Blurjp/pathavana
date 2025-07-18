import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Trips from './Trips';
import { Trip, TravelSession } from '../types';
import { travelApi } from '../services/travelApi';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { AuthProvider } from '../contexts/AuthContext';

// Mock the API services
jest.mock('../services/travelApi', () => ({
  travelApi: {
    getTrips: jest.fn(),
    deleteTrip: jest.fn()
  }
}));

jest.mock('../services/unifiedTravelApi', () => ({
  unifiedTravelApi: {
    getUserSessions: jest.fn()
  }
}));
jest.mock('../utils/errorHandler', () => ({
  handleApiError: (error: any) => error.message || 'An error occurred'
}));

// Mock AuthGuard to always render children
jest.mock('../components/auth/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

// Mock date helpers
jest.mock('../utils/dateHelpers', () => ({
  formatDate: (date: string) => {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  },
  formatDateTime: (date: string) => {
    const d = new Date(date);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });
  }
}));

const mockTrips: Trip[] = [
  {
    id: '1',
    name: 'Summer Vacation in Hawaii',
    description: 'Two weeks in paradise',
    destination: 'Hawaii, USA',
    startDate: '2024-06-15',
    endDate: '2024-06-29',
    travelers: [
      { id: '1', name: 'John Doe' },
      { id: '2', name: 'Jane Doe' }
    ],
    itinerary: [
      {
        id: 'item-1',
        type: 'flight',
        title: 'Flight to Honolulu',
        startTime: '2024-06-15T10:00:00',
        endTime: '2024-06-15T15:00:00',
        status: 'booked'
      },
      {
        id: 'item-2',
        type: 'hotel',
        title: 'Waikiki Beach Resort',
        startTime: '2024-06-15T16:00:00',
        endTime: '2024-06-29T11:00:00',
        status: 'booked'
      },
      {
        id: 'item-3',
        type: 'activity',
        title: 'Snorkeling Tour',
        startTime: '2024-06-17T09:00:00',
        endTime: '2024-06-17T12:00:00',
        status: 'planned'
      }
    ],
    budget: 5000,
    status: 'booked',
    createdAt: '2024-03-01T10:00:00',
    updatedAt: '2024-03-15T14:30:00'
  },
  {
    id: '2',
    name: 'European Adventure',
    destination: 'Paris, Rome, Barcelona',
    startDate: '2024-09-01',
    endDate: '2024-09-21',
    travelers: [{ id: '1', name: 'John Doe' }],
    itinerary: [],
    budget: 8000,
    status: 'planning',
    createdAt: '2024-03-20T09:00:00',
    updatedAt: '2024-03-20T09:00:00'
  }
];

const mockSessions: TravelSession[] = [
  {
    id: 'session-1',
    userId: 'user-1',
    messages: [
      { id: '1', type: 'user', content: 'I want to plan a trip to Japan', timestamp: '2024-03-25T10:00:00' },
      { id: '2', type: 'assistant', content: 'Great! When would you like to visit Japan?', timestamp: '2024-03-25T10:00:30' }
    ],
    context: {
      currentRequest: {
        query: 'Trip to Japan',
        destination: 'Japan',
        departureDate: '2024-10-01',
        returnDate: '2024-10-14',
        travelers: 1,
        timestamp: '2024-03-25T10:00:00'
      },
      searchHistory: [],
      selectedOptions: {}
    },
    status: 'active',
    createdAt: '2024-03-25T10:00:00',
    updatedAt: '2024-03-25T10:30:00'
  }
];

describe('Trips Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set up default mock responses
    (travelApi.getTrips as jest.Mock).mockResolvedValue({
      success: true,
      data: mockTrips
    });
    (unifiedTravelApi.getUserSessions as jest.Mock).mockResolvedValue({
      success: true,
      data: mockSessions
    });
  });

  const renderTripsPage = () => {
    return render(
      <MemoryRouter initialEntries={['/trips']}>
        <AuthProvider>
          <Routes>
            <Route path="/trips" element={<Trips />} />
            <Route path="/chat" element={<div>Chat Page</div>} />
            <Route path="/chat/:sessionId" element={<div>Chat Session Page</div>} />
            <Route path="/trips/:tripId" element={<div>Trip Details Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  describe('Page Loading and Navigation', () => {
    it('should render the page header with correct title and action button', async () => {
      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('My Trips')).toBeInTheDocument();
        expect(screen.getByText('Plan New Trip')).toBeInTheDocument();
      });
    });

    it('should navigate to chat page when Plan New Trip is clicked', async () => {
      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Plan New Trip')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Plan New Trip'));
      
      await waitFor(() => {
        expect(screen.getByText('Chat Page')).toBeInTheDocument();
      });
    });

    it('should show loading state while fetching data', () => {
      // Delay the API response
      (travelApi.getTrips as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true, data: mockTrips }), 100))
      );

      renderTripsPage();

      expect(screen.getByText('Loading your trips...')).toBeInTheDocument();
      expect(document.querySelector('.loading-spinner')).toBeInTheDocument();
    });

    it('should show error state when API fails', async () => {
      (travelApi.getTrips as jest.Mock).mockRejectedValue(new Error('Network error'));

      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    it('should retry loading when Try Again is clicked', async () => {
      (travelApi.getTrips as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ success: true, data: mockTrips });

      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should render both tabs with correct counts', async () => {
      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Saved Trips (2)')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Planning Sessions/ })).toBeInTheDocument();
      });
    });

    it('should show saved trips by default', async () => {
      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
        expect(screen.getByText('European Adventure')).toBeInTheDocument();
      });
    });

    it('should switch to planning sessions when tab is clicked', async () => {
      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Planning Sessions (0)')).toBeInTheDocument();
      });

      const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
      fireEvent.click(planningTab);

      await waitFor(() => {
        expect(screen.getByText('Planning Sessions (1)')).toBeInTheDocument();
        expect(screen.getByText('Planning Session')).toBeInTheDocument();
        expect(screen.getByText('Planning for:')).toBeInTheDocument();
        expect(screen.getByText('Japan')).toBeInTheDocument();
      });
    });

    it('should maintain active tab styling', async () => {
      renderTripsPage();

      await waitFor(() => {
        const savedTab = screen.getByRole('button', { name: /Saved Trips/ });
        expect(savedTab).toHaveClass('active');
      });

      const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
      fireEvent.click(planningTab);

      await waitFor(() => {
        const planningTabAfter = screen.getByRole('button', { name: /Planning Sessions/ });
        const savedTab = screen.getByRole('button', { name: /Saved Trips/ });
        expect(planningTabAfter).toHaveClass('active');
        expect(savedTab).not.toHaveClass('active');
      });
    });
  });

  describe('Trip Card Display', () => {
    it('should display all trip information correctly', async () => {
      renderTripsPage();

      await waitFor(() => {
        const hawaiiTrip = screen.getByText('Summer Vacation in Hawaii').closest('.trip-card') as HTMLElement;
        expect(hawaiiTrip).toBeInTheDocument();
        
        // Check all trip details
        expect(within(hawaiiTrip).getByText('✈️ booked')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('Hawaii, USA')).toBeInTheDocument();
        // Date formatting should match mocked formatDate function
        const dateRange = within(hawaiiTrip).getByText((content, element) => {
          return content.includes('Jun') && content.includes('2024');
        });
        expect(dateRange).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('John Doe, Jane Doe')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('$5,000')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('Two weeks in paradise')).toBeInTheDocument();
      });
    });

    it('should display correct status icons and colors', async () => {
      renderTripsPage();

      await waitFor(() => {
        const bookedTrip = screen.getByText('✈️ booked');
        const planningTrip = screen.getByText('📋 planning');
        
        expect(bookedTrip.closest('.status')).toHaveClass('green');
        expect(planningTrip.closest('.status')).toHaveClass('blue');
      });
    });

    it('should show itinerary preview with correct item count', async () => {
      renderTripsPage();

      await waitFor(() => {
        const hawaiiTrip = screen.getByText('Summer Vacation in Hawaii').closest('.trip-card') as HTMLElement;
        
        expect(within(hawaiiTrip).getByText('Itinerary Preview')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('Flight to Honolulu')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('Waikiki Beach Resort')).toBeInTheDocument();
        expect(within(hawaiiTrip).getByText('Snorkeling Tour')).toBeInTheDocument();
      });
    });

    it('should show View Details and Delete buttons', async () => {
      renderTripsPage();

      await waitFor(() => {
        const trips = screen.getAllByText('View Details');
        const deleteButtons = screen.getAllByText('Delete');
        
        expect(trips).toHaveLength(2);
        expect(deleteButtons).toHaveLength(2);
      });
    });

    it('should navigate to trip details when View Details is clicked', async () => {
      renderTripsPage();

      await waitFor(() => {
        const viewDetailsButtons = screen.getAllByText('View Details');
        fireEvent.click(viewDetailsButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Trip Details Page')).toBeInTheDocument();
      });
    });
  });

  describe('Trip Deletion', () => {
    it('should show confirmation dialog when delete is clicked', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
      
      renderTripsPage();

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this trip?');
      confirmSpy.mockRestore();
    });

    it('should delete trip when confirmed', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);
      (travelApi.deleteTrip as jest.Mock).mockResolvedValue({ success: true });

      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(travelApi.deleteTrip).toHaveBeenCalledWith('1');
        expect(screen.queryByText('Summer Vacation in Hawaii')).not.toBeInTheDocument();
        expect(screen.getByText('European Adventure')).toBeInTheDocument();
      });
    });

    it('should not delete trip when cancelled', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(false);

      renderTripsPage();

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      expect(travelApi.deleteTrip).not.toHaveBeenCalled();
      expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
    });

    it('should show error message when deletion fails', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);
      (travelApi.deleteTrip as jest.Mock).mockRejectedValue(new Error('Failed to delete'));

      renderTripsPage();

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to delete')).toBeInTheDocument();
        expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
      });
    });
  });

  describe('Empty States', () => {
    it('should show empty state for saved trips', async () => {
      (travelApi.getTrips as jest.Mock).mockResolvedValue({ success: true, data: [] });

      renderTripsPage();

      await waitFor(() => {
        expect(screen.getByText('No saved trips yet')).toBeInTheDocument();
        expect(screen.getByText('Start planning your first trip to see it here')).toBeInTheDocument();
        expect(screen.getByText('Plan Your First Trip')).toBeInTheDocument();
      });
    });

    it('should show empty state for planning sessions', async () => {
      (unifiedTravelApi.getUserSessions as jest.Mock).mockResolvedValue({ success: true, data: [] });

      renderTripsPage();

      const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
      fireEvent.click(planningTab);

      await waitFor(() => {
        expect(screen.getByText('No active planning sessions')).toBeInTheDocument();
        expect(screen.getByText('Start a conversation to begin planning a trip')).toBeInTheDocument();
        expect(screen.getByText('Start Planning')).toBeInTheDocument();
      });
    });
  });

  describe('Planning Sessions', () => {
    it('should display session information correctly', async () => {
      renderTripsPage();

      const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
      fireEvent.click(planningTab);

      await waitFor(() => {
        const sessionCard = screen.getByText('Planning Session').closest('.session-card') as HTMLElement;
        expect(sessionCard).toBeInTheDocument();
        
        expect(within(sessionCard).getByText('active')).toBeInTheDocument();
        expect(within(sessionCard).getByText('2')).toBeInTheDocument(); // message count
        expect(within(sessionCard).getByText('Japan')).toBeInTheDocument();
        expect(within(sessionCard).getByText('Continue')).toBeInTheDocument();
      });
    });

    it('should navigate to chat session when Continue is clicked', async () => {
      renderTripsPage();

      const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
      fireEvent.click(planningTab);

      // Wait for sessions to load and Continue button to appear
      await waitFor(() => {
        expect(screen.getByText('Continue')).toBeInTheDocument();
      });

      // Click the Continue button
      fireEvent.click(screen.getByText('Continue'));

      // Since we're using MemoryRouter, we won't actually navigate
      // Just verify the link is correct
      const continueLink = screen.getByText('Continue').closest('a');
      expect(continueLink).toHaveAttribute('href', '/chat/session-1');
    });
  });

  describe('Date Formatting', () => {
    it('should format dates correctly', async () => {
      renderTripsPage();

      await waitFor(() => {
        // Wait for trips to be loaded
        expect(screen.getByText('Summer Vacation in Hawaii')).toBeInTheDocument();
      });

      // Check that date elements are rendered (they appear in the trip cards)
      const tripCard = screen.getByText('Summer Vacation in Hawaii').closest('.trip-card');
      expect(tripCard).toBeInTheDocument();
      
      // Verify the dates are shown in the card
      expect(screen.getByText(/2024/)).toBeInTheDocument();
    });
  });
});