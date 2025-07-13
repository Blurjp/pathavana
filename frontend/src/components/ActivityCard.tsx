import React, { useState } from 'react';
import { ActivityOption } from '../types';
import PriceDisplay from './PriceDisplay';
import RatingStars from './RatingStars';
import AmenityIcons from './AmenityIcons';
import './ActivityCard.css';

interface ActivityCardProps {
  activity: ActivityOption;
  isSelected?: boolean;
  onSelect?: () => void;
  showFullDetails?: boolean;
  onAddToTrip?: () => void;
  participants?: number;
  previousPrice?: { amount: number; currency: string; displayPrice: string };
}

const ActivityCard: React.FC<ActivityCardProps> = ({
  activity,
  isSelected = false,
  onSelect,
  showFullDetails = false,
  onAddToTrip,
  participants = 1,
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
    return '/images/activity-placeholder.jpg';
  };

  const images = activity.images && activity.images.length > 0 ? activity.images : [getDefaultImage()];

  const nextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const calculateTotalPrice = (): { amount: number; currency: string; displayPrice: string } => {
    const totalAmount = activity.price.amount * participants;
    return {
      amount: totalAmount,
      currency: activity.price.currency,
      displayPrice: `${activity.price.currency} ${totalAmount.toLocaleString()}`
    };
  };

  const getActivityTypeIcon = (type: string): string => {
    const typeIcons: Record<string, string> = {
      'tour': '🗺️',
      'adventure': '🏔️',
      'cultural': '🏛️',
      'food': '🍽️',
      'entertainment': '🎭',
      'outdoor': '🌲',
      'museum': '🏛️',
      'shopping': '🛍️',
      'nightlife': '🌃',
      'sports': '⚽',
      'nature': '🌿',
      'historical': '🏰',
      'art': '🎨',
      'music': '🎵',
      'photography': '📸',
      'water sports': '🏄',
      'extreme sports': '🪂',
      'family': '👨‍👩‍👧‍👦',
      'couples': '💕',
      'solo': '🚶'
    };
    
    const normalizedType = type.toLowerCase();
    return typeIcons[normalizedType] || '🎯';
  };

  const getGroupSizeDiscount = (): number | null => {
    if (participants >= 4) {
      return 15; // 15% discount for groups of 4+
    } else if (participants >= 2) {
      return 10; // 10% discount for groups of 2+
    }
    return null;
  };

  const getIncludedItems = (): string[] => {
    // This would come from the activity data in a real implementation
    const commonInclusions = [
      'Professional guide',
      'Transportation',
      'Entrance fees',
      'Equipment rental',
      'Insurance coverage',
      'Light refreshments',
      'Photos included',
      'Small group experience'
    ];
    return commonInclusions.slice(0, Math.floor(Math.random() * 5) + 3);
  };

  const getExcludedItems = (): string[] => {
    // This would come from the activity data in a real implementation
    const commonExclusions = [
      'Personal expenses',
      'Meals (unless specified)',
      'Tips and gratuities',
      'Hotel pickup (available for extra cost)',
      'Travel insurance',
      'Alcoholic beverages'
    ];
    return commonExclusions.slice(0, Math.floor(Math.random() * 4) + 2);
  };

  const getMeetingPoint = (): string => {
    // This would come from the activity data in a real implementation
    return `${activity.location.address} - Meeting point will be confirmed in your booking confirmation`;
  };

  const getAvailableDates = (): string[] => {
    // This would come from the activity data in a real implementation
    const today = new Date();
    const dates = [];
    for (let i = 1; i <= 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        weekday: 'short'
      }));
    }
    return dates;
  };

  const formatDuration = (duration?: string): string => {
    if (!duration) return 'Duration not specified';
    return duration;
  };

  const totalPrice = calculateTotalPrice();
  const groupDiscount = getGroupSizeDiscount();
  const includedItems = getIncludedItems();
  const excludedItems = getExcludedItems();
  const availableDates = getAvailableDates();

  return (
    <div 
      className={`activity-card ${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={handleCardClick}
    >
      {/* Activity image carousel */}
      <div className="activity-image-container">
        <div className="activity-image">
          <img
            src={images[currentImageIndex]}
            alt={activity.name}
            onError={(e) => {
              if (!imageError) {
                setImageError(true);
                const target = e.target as HTMLImageElement;
                target.src = getDefaultImage();
              }
            }}
          />
          
          {/* Activity type badge */}
          <div className="activity-type-badge">
            <span className="type-icon">{getActivityTypeIcon(activity.type)}</span>
            <span className="type-label">{activity.type}</span>
          </div>
          
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

      {/* Activity content */}
      <div className="activity-content">
        <div className="activity-header">
          <div className="activity-title">
            <h4 className="activity-name">{activity.name}</h4>
            <div className="activity-meta">
              {activity.duration && (
                <span className="duration">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                    <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  {formatDuration(activity.duration)}
                </span>
              )}
              
              {activity.rating && (
                <div className="activity-rating">
                  <RatingStars 
                    rating={activity.rating}
                    size="small"
                    showValue={true}
                  />
                </div>
              )}
            </div>
          </div>
          
          <div className="price-section">
            <PriceDisplay 
              price={activity.price}
              size="large"
              style="prominent"
              showChangeIndicator={!!previousPrice}
              previousPrice={previousPrice}
            />
            <span className="price-period">/person</span>
            
            {participants > 1 && (
              <div className="total-price">
                <span className="total-label">Total ({participants} people):</span>
                <PriceDisplay 
                  price={totalPrice}
                  size="medium"
                  style="default"
                />
                {groupDiscount && (
                  <span className="discount-badge">
                    {groupDiscount}% group discount applied!
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="activity-description">
          <p className={isExpanded ? 'expanded' : 'truncated'}>
            {activity.description}
          </p>
        </div>

        {/* Location info */}
        <div className="location-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" stroke="currentColor" strokeWidth="2"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" strokeWidth="2"/>
          </svg>
          <span className="location-text">{activity.location.city}, {activity.location.country}</span>
        </div>

        {/* Quick highlights */}
        <div className="activity-highlights">
          <div className="highlight-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2"/>
              <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="2"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" strokeWidth="2"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>Small group experience</span>
          </div>
          
          <div className="highlight-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2"/>
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>Free cancellation</span>
          </div>
          
          <div className="highlight-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M14 9V5a3 3 0 0 0-6 0v4" stroke="currentColor" strokeWidth="2"/>
              <rect x="2" y="9" width="20" height="12" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span>Instant confirmation</span>
          </div>
        </div>

        {/* Expandable details */}
        {isExpanded && (
          <div className="activity-details">
            <div className="details-section">
              <h5>What's Included</h5>
              <ul className="included-list">
                {includedItems.map((item, index) => (
                  <li key={index} className="included-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <path d="M9 12l2 2 4-4" stroke="var(--success-color)" strokeWidth="2"/>
                      <circle cx="12" cy="12" r="10" stroke="var(--success-color)" strokeWidth="2"/>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="details-section">
              <h5>What's Not Included</h5>
              <ul className="excluded-list">
                {excludedItems.map((item, index) => (
                  <li key={index} className="excluded-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="var(--error-color)" strokeWidth="2"/>
                      <path d="M15 9l-6 6" stroke="var(--error-color)" strokeWidth="2"/>
                      <path d="M9 9l6 6" stroke="var(--error-color)" strokeWidth="2"/>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="details-section">
              <h5>Meeting Point</h5>
              <p className="meeting-point">{getMeetingPoint()}</p>
            </div>
            
            <div className="details-section">
              <h5>Available Dates</h5>
              <div className="available-dates">
                {availableDates.map((date, index) => (
                  <button
                    key={index}
                    className="date-option"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle date selection
                    }}
                  >
                    {date}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="activity-actions">
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
              'Select Activity'
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

export default ActivityCard;