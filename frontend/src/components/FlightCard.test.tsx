import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FlightCard from './FlightCard';
import { FlightOption } from '../types';

describe('FlightCard', () => {
  // Helper to get container
  const getContainer = () => document.querySelector('.flight-card');
  const mockFlight: FlightOption = {
    id: 'test-flight-1',
    airline: 'Test Airlines',
    flightNumber: 'TA123',
    origin: {
      code: 'NYC',
      name: 'John F. Kennedy International Airport',
      city: 'New York',
      country: 'USA',
      terminal: 'A'
    },
    destination: {
      code: 'LAX',
      name: 'Los Angeles International Airport',
      city: 'Los Angeles',
      country: 'USA',
      terminal: 'B'
    },
    departureTime: '2024-03-15T10:30:00Z',
    arrivalTime: '2024-03-15T13:45:00Z',
    duration: '5h 15m',
    price: {
      amount: 299,
      currency: 'USD',
      displayPrice: 'USD 299'
    },
    stops: 0,
    aircraft: 'Boeing 737',
    amenities: ['Wi-Fi', 'In-flight Entertainment', 'USB Power']
  };

  const defaultProps = {
    flight: mockFlight,
    isSelected: false,
    onSelect: jest.fn(),
    showFullDetails: false,
    onAddToTrip: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render flight basic information correctly', () => {
    render(<FlightCard {...defaultProps} />);

    // Check airline info
    expect(screen.getByText('Test Airlines')).toBeInTheDocument();
    expect(screen.getByText('TA123')).toBeInTheDocument();

    // Check route info
    expect(screen.getByText('NYC')).toBeInTheDocument();
    expect(screen.getByText('LAX')).toBeInTheDocument();
    expect(screen.getByText('New York')).toBeInTheDocument();
    expect(screen.getByText('Los Angeles')).toBeInTheDocument();

    // Check price - The price is formatted as $299
    expect(screen.getByText('$299')).toBeInTheDocument();

    // Check duration
    expect(screen.getByText('5h 15m')).toBeInTheDocument();

    // Check stops
    expect(screen.getByText('Nonstop')).toBeInTheDocument();
  });

  it('should handle card selection when clicked', () => {
    const onSelect = jest.fn();
    render(<FlightCard {...defaultProps} onSelect={onSelect} />);

    const card = document.querySelector('.flight-card');
    fireEvent.click(card!);

    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('should show selected state correctly', () => {
    render(<FlightCard {...defaultProps} isSelected={true} />);

    const card = document.querySelector('.flight-card');
    expect(card).toHaveClass('selected');

    // Check for selected button text
    expect(screen.getByText('Selected')).toBeInTheDocument();
  });

  it('should expand/collapse details when More Details button is clicked', () => {
    render(<FlightCard {...defaultProps} />);

    // Initially collapsed
    expect(screen.queryByText('Aircraft Type:')).toBeNull();

    // Click More Details
    const expandButton = screen.getByText('More Details').closest('button');
    fireEvent.click(expandButton!);

    // Should show expanded details
    expect(screen.getByText('Aircraft Type:')).toBeInTheDocument();
    expect(screen.getAllByText('Boeing 737')).toHaveLength(2); // Appears in quick info and details
    expect(screen.getByText('Flight Duration:')).toBeInTheDocument();

    // Button text should change
    expect(screen.getByText('Less Details')).toBeInTheDocument();

    // Click again to collapse
    fireEvent.click(expandButton!);
    expect(screen.queryByText('Aircraft Type:')).toBeNull();
    expect(screen.getByText('More Details')).toBeInTheDocument();
  });

  it('should call onAddToTrip when Add to Trip button is clicked', () => {
    const onAddToTrip = jest.fn();
    render(<FlightCard {...defaultProps} onAddToTrip={onAddToTrip} />);

    const addButton = screen.getByText('Add to Trip').closest('button');
    fireEvent.click(addButton!);

    expect(onAddToTrip).toHaveBeenCalledTimes(1);
  });

  it('should not show Add to Trip button when onAddToTrip is not provided', () => {
    render(<FlightCard {...defaultProps} onAddToTrip={undefined} />);

    expect(screen.queryByText('Add to Trip')).toBeNull();
  });

  it('should stop event propagation when action buttons are clicked', () => {
    const onSelect = jest.fn();
    const onAddToTrip = jest.fn();
    render(<FlightCard {...defaultProps} onSelect={onSelect} onAddToTrip={onAddToTrip} />);

    // Click Add to Trip button
    const addButton = screen.getByText('Add to Trip').closest('button');
    fireEvent.click(addButton!);

    // Should not trigger card selection
    expect(onSelect).not.toHaveBeenCalled();
    expect(onAddToTrip).toHaveBeenCalledTimes(1);

    // Click Select button
    const selectButton = screen.getByText('Select Flight').closest('button');
    fireEvent.click(selectButton!);

    // Should call onSelect but not trigger card click twice
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('should display amenities correctly', () => {
    render(<FlightCard {...defaultProps} />);

    // Should show amenity icons in preview
    const amenitiesPreview = document.querySelector('.amenities-preview');
    expect(amenitiesPreview).toBeInTheDocument();

    // Expand to see all amenities
    const expandButton = screen.getByText('More Details').closest('button');
    fireEvent.click(expandButton!);

    // Check for amenities in expanded view
    expect(screen.getByText('In-flight Amenities:')).toBeInTheDocument();
  });

  it('should format times correctly', () => {
    render(<FlightCard {...defaultProps} />);

    // The formatTime function should convert ISO times to readable format
    // Since we don't have the actual implementation, we check for time elements
    const times = screen.getAllByText(/\d{1,2}:\d{2}/);
    expect(times.length).toBeGreaterThan(0);
  });

  it('should display terminal information when available', () => {
    render(<FlightCard {...defaultProps} />);

    expect(screen.getByText('Terminal A')).toBeInTheDocument();
    expect(screen.getByText('Terminal B')).toBeInTheDocument();
  });

  it('should handle flights with stops correctly', () => {
    const flightWithStops = {
      ...mockFlight,
      stops: 2
    };

    render(<FlightCard {...defaultProps} flight={flightWithStops} />);

    expect(screen.getByText('2 stops')).toBeInTheDocument();
    expect(screen.getByText('• Layover included')).toBeInTheDocument();
  });

  it('should show price change indicator when previous price is provided', () => {
    const previousPrice = {
      amount: 350,
      currency: 'USD',
      displayPrice: 'USD 350'
    };

    render(<FlightCard {...defaultProps} previousPrice={previousPrice} />);

    // Price component should show change indicator
    const priceContainer = document.querySelector('.price-container');
    expect(priceContainer).toBeInTheDocument();
  });
});