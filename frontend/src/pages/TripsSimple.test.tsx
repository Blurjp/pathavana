import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import Trips from './Trips';
import { travelApi } from '../services/travelApi';
import { unifiedTravelApi } from '../services/unifiedTravelApi';

// Mock the services
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

// Mock AuthGuard
jest.mock('../components/auth/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

// Mock date helpers
jest.mock('../utils/dateHelpers', () => ({
  formatDate: (date: string) => new Date(date).toLocaleDateString(),
  formatDateTime: (date: string) => new Date(date).toLocaleString()
}));

jest.mock('../utils/errorHandler', () => ({
  handleApiError: (error: any) => error.message || 'An error occurred'
}));

// Mock config service to prevent network calls
jest.mock('../services/configService', () => ({
  configService: {
    getApiBaseUrl: jest.fn().mockResolvedValue('http://localhost:8001'),
    getConfig: jest.fn().mockResolvedValue({
      apiBaseUrl: 'http://localhost:8001',
      features: {}
    })
  }
}));

const mockTrips = [
  {
    id: '1',
    name: 'Hawaii Trip',
    destination: 'Hawaii',
    startDate: '2024-06-15',
    endDate: '2024-06-29',
    travelers: [{ id: '1', name: 'John' }],
    itinerary: [],
    status: 'booked' as const,
    createdAt: '2024-03-01T10:00:00',
    updatedAt: '2024-03-01T10:00:00'
  }
];

const mockSessions = [
  {
    id: 'session-1',
    userId: 'user-1',
    messages: [],
    context: {},
    status: 'active' as const,
    createdAt: '2024-03-25T10:00:00',
    updatedAt: '2024-03-25T10:00:00'
  }
];

describe('Trips Page - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (travelApi.getTrips as jest.Mock).mockResolvedValue({
      success: true,
      data: mockTrips
    });
    (unifiedTravelApi.getUserSessions as jest.Mock).mockResolvedValue({
      success: true,
      data: mockSessions
    });
  });

  it('should render page title', async () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    expect(screen.getByText('My Trips')).toBeInTheDocument();
  });

  it('should load and display trips', async () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Hawaii Trip')).toBeInTheDocument();
    });
  });

  it('should show loading state initially', () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    expect(screen.getByText('Loading your trips...')).toBeInTheDocument();
  });

  it('should switch between tabs', async () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Hawaii Trip')).toBeInTheDocument();
    });

    // Click on planning sessions tab
    const planningTab = screen.getByRole('button', { name: /Planning Sessions/ });
    fireEvent.click(planningTab);

    // Should call getUserSessions
    await waitFor(() => {
      expect(unifiedTravelApi.getUserSessions).toHaveBeenCalled();
    });
  });

  it('should handle delete trip', async () => {
    window.confirm = jest.fn().mockReturnValue(true);
    (travelApi.deleteTrip as jest.Mock).mockResolvedValue({ success: true });

    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Hawaii Trip')).toBeInTheDocument();
    });

    // Click delete button
    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this trip?');
    expect(travelApi.deleteTrip).toHaveBeenCalledWith('1');
  });

  it('should show empty state when no trips', async () => {
    (travelApi.getTrips as jest.Mock).mockResolvedValue({
      success: true,
      data: []
    });

    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No saved trips yet')).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    (travelApi.getTrips as jest.Mock).mockResolvedValue({
      success: false,
      error: 'Failed to load trips'
    });

    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load trips')).toBeInTheDocument();
    });
  });

  it('should have Plan New Trip button', async () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    const planButton = screen.getByText('Plan New Trip');
    expect(planButton).toBeInTheDocument();
    expect(planButton.closest('a')).toHaveAttribute('href', '/chat');
  });

  it('should display trip details correctly', async () => {
    render(
      <MemoryRouter>
        <Trips />
      </MemoryRouter>
    );

    await waitFor(() => {
      const tripCard = screen.getByText('Hawaii Trip').closest('.trip-card');
      expect(tripCard).toBeInTheDocument();
      
      // Check status
      expect(screen.getByText('✈️ booked')).toBeInTheDocument();
      
      // Check destination
      expect(screen.getByText('Hawaii')).toBeInTheDocument();
      
      // Check View Details button
      expect(screen.getByText('View Details')).toBeInTheDocument();
    });
  });
});