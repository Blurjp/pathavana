import React, { useState } from 'react';
import { HotelOption } from '../types';
import PriceDisplay from './PriceDisplay';
import RatingStars from './RatingStars';
import AmenityIcons from './AmenityIcons';
import './HotelCard.css';

interface HotelCardProps {
  hotel: HotelOption;
  isSelected?: boolean;
  onSelect?: () => void;
  showFullDetails?: boolean;
  onAddToTrip?: () => void;
  nights?: number;
  previousPrice?: { amount: number; currency: string; displayPrice: string };
}

const HotelCard: React.FC<HotelCardProps> = ({
  hotel,
  isSelected = false,
  onSelect,
  showFullDetails = false,
  onAddToTrip,
  nights = 1,
  previousPrice
}) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(showFullDetails);
  const [imageError, setImageError] = useState(false);

  const handleCardClick = () => {
    if (onSelect) {
      onSelect();
    }
  };

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const getDefaultImage = (): string => {
    return '/images/hotel-placeholder.jpg';
  };

  const images = hotel.images && hotel.images.length > 0 ? hotel.images : [getDefaultImage()];

  const nextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const calculateTotalPrice = (): { amount: number; currency: string; displayPrice: string } => {
    const totalAmount = hotel.price.amount * nights;
    return {
      amount: totalAmount,
      currency: hotel.price.currency,
      displayPrice: `${hotel.price.currency} ${totalAmount.toLocaleString()}`
    };
  };

  const getDistanceFromCenter = (): string => {
    // This would come from the hotel data in a real implementation
    const distances = ['0.5 km', '1.2 km', '2.1 km', '3.5 km', '5.0 km'];
    return distances[Math.floor(Math.random() * distances.length)];
  };

  const getCancellationPolicy = (): string => {
    // This would come from the hotel data in a real implementation
    const policies = [
      'Free cancellation until 24 hours before check-in',
      'Free cancellation until 48 hours before check-in',
      'Non-refundable',
      'Free cancellation until 7 days before check-in'
    ];
    return policies[Math.floor(Math.random() * policies.length)];
  };

  const totalPrice = calculateTotalPrice();

  return (
    <div 
      className={`hotel-card ${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={handleCardClick}
    >
      {/* Hotel image carousel */}
      <div className="hotel-image-container">
        <div className="hotel-image">
          <img
            src={images[currentImageIndex]}
            alt={hotel.name}
            onError={(e) => {
              if (!imageError) {
                setImageError(true);
                const target = e.target as HTMLImageElement;
                target.src = getDefaultImage();
              }
            }}
          />
          
          {/* Image navigation */}
          {images.length > 1 && (
            <>
              <button 
                className="image-nav prev"
                onClick={prevImage}
                aria-label="Previous image"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </button>
              <button 
                className="image-nav next"
                onClick={nextImage}
                aria-label="Next image"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </button>
              
              {/* Image indicators */}
              <div className="image-indicators">
                {images.map((_, index) => (
                  <button
                    key={index}
                    className={`indicator ${index === currentImageIndex ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentImageIndex(index);
                    }}
                    aria-label={`Go to image ${index + 1}`}
                  />
                ))}
              </div>
            </>
          )}
          
          {/* Selection overlay */}
          {isSelected && (
            <div className="selection-overlay">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="var(--primary-color)"/>
                <path d="M8 12l2 2 4-4" stroke="white" strokeWidth="2"/>
              </svg>
            </div>
          )}
        </div>
      </div>

      {/* Hotel details */}
      <div className="hotel-content">
        <div className="hotel-header">
          <div className="hotel-title">
            <h4 className="hotel-name">{hotel.name}</h4>
            <div className="hotel-rating">
              <RatingStars 
                rating={hotel.rating}
                size="medium"
                showValue={false}
              />
            </div>
          </div>
          
          <div className="price-section">
            <PriceDisplay 
              price={hotel.price}
              size="large"
              style="prominent"
              showChangeIndicator={!!previousPrice}
              previousPrice={previousPrice}
            />
            <span className="price-period">/night</span>
            
            {nights > 1 && (
              <div className="total-price">
                <span className="total-label">Total ({nights} nights):</span>
                <PriceDisplay 
                  price={totalPrice}
                  size="medium"
                  style="default"
                />
              </div>
            )}
          </div>
        </div>

        {/* Reviews and location */}
        <div className="hotel-info">
          {hotel.reviewScore && hotel.reviewCount && (
            <div className="reviews-info">
              <div className="review-score">
                <span className="score">{hotel.reviewScore}</span>
                <span className="score-label">/10</span>
              </div>
              <div className="review-details">
                <span className="review-label">Excellent</span>
                <span className="review-count">({hotel.reviewCount.toLocaleString()} reviews)</span>
              </div>
            </div>
          )}
          
          <div className="location-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" stroke="currentColor" strokeWidth="2"/>
              <circle cx="12" cy="10" r="3" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <div className="location-details">
              <span className="address">{hotel.location.address}</span>
              <span className="distance">{getDistanceFromCenter()} from city center</span>
            </div>
          </div>
        </div>

        {/* Amenities preview */}
        <div className="amenities-section">
          <AmenityIcons 
            amenities={hotel.amenities}
            maxVisible={isExpanded ? hotel.amenities.length : 6}
            size="medium"
            showLabels={false}
            layout="horizontal"
          />
        </div>

        {/* Description preview */}
        {hotel.description && (
          <div className="description-preview">
            <p className={isExpanded ? 'expanded' : 'truncated'}>
              {hotel.description}
            </p>
          </div>
        )}

        {/* Expandable details */}
        {isExpanded && (
          <div className="hotel-details">
            <div className="details-section">
              <h5>Hotel Amenities</h5>
              <AmenityIcons 
                amenities={hotel.amenities}
                showLabels={true}
                layout="grid"
                size="medium"
              />
            </div>
            
            <div className="details-section">
              <h5>Policies</h5>
              <div className="policy-item">
                <span className="policy-label">Cancellation:</span>
                <span className="policy-value">{getCancellationPolicy()}</span>
              </div>
              <div className="policy-item">
                <span className="policy-label">Check-in:</span>
                <span className="policy-value">3:00 PM - 12:00 AM</span>
              </div>
              <div className="policy-item">
                <span className="policy-label">Check-out:</span>
                <span className="policy-value">12:00 PM</span>
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="hotel-actions">
          <button 
            className="btn-secondary expand-btn"
            onClick={toggleExpanded}
            aria-expanded={isExpanded}
          >
            <span>{isExpanded ? 'Less Details' : 'More Details'}</span>
            <svg 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none"
              className={`expand-icon ${isExpanded ? 'rotated' : ''}`}
            >
              <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
          
          {onAddToTrip && (
            <button 
              className="btn-secondary add-to-trip"
              onClick={(e) => {
                e.stopPropagation();
                onAddToTrip();
              }}
              title="Add to trip"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 5v14m-7-7h14" stroke="currentColor" strokeWidth="2"/>
              </svg>
              Add to Trip
            </button>
          )}
          
          <button 
            className={`btn-primary select-btn ${isSelected ? 'selected' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              if (onSelect) onSelect();
            }}
          >
            {isSelected ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2"/>
                </svg>
                Selected
              </>
            ) : (
              'Select Hotel'
            )}
          </button>
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="selection-indicator">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="var(--primary-color)"/>
            <path d="M8 12l2 2 4-4" stroke="white" strokeWidth="2"/>
          </svg>
        </div>
      )}
    </div>
  );
};

export default HotelCard;