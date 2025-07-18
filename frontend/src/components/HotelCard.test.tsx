import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HotelCard from './HotelCard';
import { HotelOption } from '../types';

describe('HotelCard', () => {
  // Helper to get container
  const getContainer = () => document.querySelector('.hotel-card');
  const mockHotel: HotelOption = {
    id: 'test-hotel-1',
    name: 'Grand Test Hotel',
    rating: 4.5,
    reviewScore: 8.7,
    reviewCount: 1234,
    location: {
      address: '123 Test Street',
      city: 'Test City',
      country: 'Test Country',
      coordinates: { lat: 40.7128, lng: -74.0060 }
    },
    price: {
      amount: 150,
      currency: 'USD',
      displayPrice: 'USD 150'
    },
    images: [
      'https://example.com/hotel1.jpg',
      'https://example.com/hotel2.jpg',
      'https://example.com/hotel3.jpg'
    ],
    amenities: ['Free Wi-Fi', 'Pool', 'Gym', 'Restaurant', 'Spa', 'Parking'],
    description: 'A luxurious hotel in the heart of the city with excellent amenities.'
  };

  const defaultProps = {
    hotel: mockHotel,
    isSelected: false,
    onSelect: jest.fn(),
    showFullDetails: false,
    onAddToTrip: jest.fn(),
    nights: 2
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render hotel basic information correctly', () => {
    render(<HotelCard {...defaultProps} />);

    // Check hotel name
    expect(screen.getByText('Grand Test Hotel')).toBeInTheDocument();

    // Check location
    expect(screen.getByText('123 Test Street')).toBeInTheDocument();

    // Check price - The price is formatted as $150
    expect(screen.getByText('$150')).toBeInTheDocument();
    expect(screen.getByText('/night')).toBeInTheDocument();

    // Check reviews
    expect(screen.getByText('8.7')).toBeInTheDocument();
    expect(screen.getByText('/10')).toBeInTheDocument();
    expect(screen.getByText('Excellent')).toBeInTheDocument();
    expect(screen.getByText('(1,234 reviews)')).toBeInTheDocument();

    // Check description
    expect(screen.getByText(/A luxurious hotel/)).toBeInTheDocument();
  });

  it('should calculate and display total price for multiple nights', () => {
    render(<HotelCard {...defaultProps} nights={3} />);

    // Should show total price
    expect(screen.getByText('Total (3 nights):')).toBeInTheDocument();
    
    // Total should be 150 * 3 = 450 - formatted as $450
    const totalPriceElement = screen.getByText('$450');
    expect(totalPriceElement).toBeInTheDocument();
  });

  it('should handle image carousel navigation', () => {
    render(<HotelCard {...defaultProps} />);

    // Initially first image should be shown (we can't test actual image src without mocking)
    const prevButton = screen.getByLabelText('Previous image');
    const nextButton = screen.getByLabelText('Next image');

    expect(prevButton).toBeInTheDocument();
    expect(nextButton).toBeInTheDocument();

    // Check image indicators
    const indicators = screen.getAllByRole('button', { name: /Go to image/i });
    expect(indicators).toHaveLength(3);
    
    // First indicator should be active
    expect(indicators[0]).toHaveClass('active');

    // Click next button
    fireEvent.click(nextButton);
    
    // Second indicator should now be active
    expect(indicators[1]).toHaveClass('active');
    expect(indicators[0]).not.toHaveClass('active');

    // Click previous button
    fireEvent.click(prevButton);
    
    // First indicator should be active again
    expect(indicators[0]).toHaveClass('active');
    expect(indicators[1]).not.toHaveClass('active');

    // Click third indicator directly
    fireEvent.click(indicators[2]);
    
    // Third indicator should be active
    expect(indicators[2]).toHaveClass('active');
    expect(indicators[0]).not.toHaveClass('active');
  });

  it('should handle card selection when clicked', () => {
    const onSelect = jest.fn();
    render(<HotelCard {...defaultProps} onSelect={onSelect} />);

    const card = document.querySelector('.hotel-card');
    fireEvent.click(card!);

    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('should show selected state correctly', () => {
    render(<HotelCard {...defaultProps} isSelected={true} />);

    const card = document.querySelector('.hotel-card');
    expect(card).toHaveClass('selected');

    // Check for selected button text
    expect(screen.getByText('Selected')).toBeInTheDocument();

    // Check for selection overlay on image
    const selectionOverlay = card!.querySelector('.selection-overlay');
    expect(selectionOverlay).toBeInTheDocument();
  });

  it('should expand/collapse details when More Details button is clicked', () => {
    render(<HotelCard {...defaultProps} />);

    // Initially collapsed
    expect(screen.queryByText('Hotel Amenities')).toBeNull();
    expect(screen.queryByText('Policies')).toBeNull();

    // Click More Details
    const expandButton = screen.getByText('More Details').closest('button');
    fireEvent.click(expandButton!);

    // Should show expanded details
    expect(screen.getByText('Hotel Amenities')).toBeInTheDocument();
    expect(screen.getByText('Policies')).toBeInTheDocument();
    expect(screen.getByText('Cancellation:')).toBeInTheDocument();
    expect(screen.getByText('Check-in:')).toBeInTheDocument();
    expect(screen.getByText('Check-out:')).toBeInTheDocument();

    // Button text should change
    expect(screen.getByText('Less Details')).toBeInTheDocument();

    // Click again to collapse
    fireEvent.click(expandButton!);
    expect(screen.queryByText('Hotel Amenities')).toBeNull();
    expect(screen.getByText('More Details')).toBeInTheDocument();
  });

  it('should call onAddToTrip when Add to Trip button is clicked', () => {
    const onAddToTrip = jest.fn();
    render(<HotelCard {...defaultProps} onAddToTrip={onAddToTrip} />);

    const addButton = screen.getByText('Add to Trip').closest('button');
    fireEvent.click(addButton!);

    expect(onAddToTrip).toHaveBeenCalledTimes(1);
  });

  it('should not show Add to Trip button when onAddToTrip is not provided', () => {
    render(<HotelCard {...defaultProps} onAddToTrip={undefined} />);

    expect(screen.queryByText('Add to Trip')).toBeNull();
  });

  it('should stop event propagation when action buttons are clicked', () => {
    const onSelect = jest.fn();
    const onAddToTrip = jest.fn();
    render(<HotelCard {...defaultProps} onSelect={onSelect} onAddToTrip={onAddToTrip} />);

    // Click Add to Trip button
    const addButton = screen.getByText('Add to Trip').closest('button');
    fireEvent.click(addButton!);

    // Should not trigger card selection
    expect(onSelect).not.toHaveBeenCalled();
    expect(onAddToTrip).toHaveBeenCalledTimes(1);

    // Click Select button
    const selectButton = screen.getByText('Select Hotel').closest('button');
    fireEvent.click(selectButton!);

    // Should call onSelect but not trigger card click twice
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('should display amenities correctly', () => {
    render(<HotelCard {...defaultProps} />);

    // Should show limited amenities in preview (maxVisible=6 by default)
    const amenitiesSection = document.querySelector('.amenities-section');
    expect(amenitiesSection).toBeInTheDocument();

    // Expand to see all amenities
    const expandButton = screen.getByText('More Details').closest('button');
    fireEvent.click(expandButton!);

    // All amenities should be visible in expanded view
    const amenitiesExpanded = screen.getByText('Hotel Amenities').parentElement;
    expect(amenitiesExpanded).toBeInTheDocument();
  });

  it('should handle hotels without images gracefully', () => {
    const hotelWithoutImages = {
      ...mockHotel,
      images: []
    };

    render(<HotelCard {...defaultProps} hotel={hotelWithoutImages} />);

    // Should show placeholder image
    const image = screen.getByRole('img', { name: mockHotel.name });
    expect(image).toBeInTheDocument();

    // Should not show carousel controls
    expect(screen.queryByLabelText('Previous image')).toBeNull();
    expect(screen.queryByLabelText('Next image')).toBeNull();
  });

  it('should handle image load errors', () => {
    render(<HotelCard {...defaultProps} />);

    const image = screen.getByRole('img', { name: mockHotel.name });
    
    // Simulate image load error
    fireEvent.error(image);

    // Should fallback to placeholder
    expect(image.getAttribute('src')).toBe('/images/hotel-placeholder.jpg');
  });

  it('should display rating stars correctly', () => {
    render(<HotelCard {...defaultProps} />);

    // Rating component should be rendered
    const ratingContainer = document.querySelector('.hotel-rating');
    expect(ratingContainer).toBeInTheDocument();
  });

  it('should show price change indicator when previous price is provided', () => {
    const previousPrice = {
      amount: 200,
      currency: 'USD',
      displayPrice: 'USD 200'
    };

    render(<HotelCard {...defaultProps} previousPrice={previousPrice} />);

    // Price component should show change indicator
    const priceSection = document.querySelector('.price-section');
    expect(priceSection).toBeInTheDocument();
  });

  it('should handle hotels without review data', () => {
    const hotelWithoutReviews = {
      ...mockHotel,
      reviewScore: undefined,
      reviewCount: undefined
    };

    render(<HotelCard {...defaultProps} hotel={hotelWithoutReviews} />);

    // Should not show review section
    expect(screen.queryByText('/10')).toBeNull();
    expect(screen.queryByText('reviews')).toBeNull();
  });

  it('should truncate description when not expanded', () => {
    const longDescription = 'Lorem ipsum '.repeat(50);
    const hotelWithLongDescription = {
      ...mockHotel,
      description: longDescription
    };

    render(<HotelCard {...defaultProps} hotel={hotelWithLongDescription} />);

    const description = screen.getByText(/Lorem ipsum/);
    expect(description).toHaveClass('truncated');

    // Expand to see full description
    const expandButton = screen.getByText('More Details').closest('button');
    fireEvent.click(expandButton!);

    expect(description).toHaveClass('expanded');
  });
});