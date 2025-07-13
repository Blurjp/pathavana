import React, { useState } from 'react';
import { FlightOption } from '../types';
import { formatTime, calculateDuration } from '../utils/dateHelpers';
import PriceDisplay from './PriceDisplay';
import AmenityIcons from './AmenityIcons';
import './FlightCard.css';

interface FlightCardProps {
  flight: FlightOption;
  isSelected?: boolean;
  onSelect?: () => void;
  showFullDetails?: boolean;
  onAddToTrip?: () => void;
  previousPrice?: { amount: number; currency: string; displayPrice: string };
}

const FlightCard: React.FC<FlightCardProps> = ({
  flight,
  isSelected = false,
  onSelect,
  showFullDetails = false,
  onAddToTrip,
  previousPrice
}) => {
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

  const getStopsText = (stops: number): string => {
    if (stops === 0) return 'Nonstop';
    if (stops === 1) return '1 stop';
    return `${stops} stops`;
  };

  const getAirlineLogoUrl = (airline: string): string => {
    // In a real app, you'd have actual airline logos
    // For now, return a placeholder or use airline code
    return `/images/airlines/${airline.toLowerCase().replace(/\s+/g, '-')}.png`;
  };

  const getDurationInMinutes = (duration: string): number => {
    // Parse duration string like "2h 30m" or "1h 45m"
    const hours = duration.match(/(\d+)h/);
    const minutes = duration.match(/(\d+)m/);
    return (hours ? parseInt(hours[1]) * 60 : 0) + (minutes ? parseInt(minutes[1]) : 0);
  };

  const getFlightClass = (): string => {
    // This would come from the flight data in a real implementation
    return 'Economy'; // Default for now
  };

  const formatDuration = (duration: string): string => {
    const totalMinutes = getDurationInMinutes(duration);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${hours}h ${minutes > 0 ? `${minutes}m` : ''}`.trim();
  };

  return (
    <div 
      className={`flight-card ${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={handleCardClick}
    >
      {/* Flight header */}
      <div className="flight-header">
        <div className="airline-info">
          <div className="airline-logo-container">
            {!imageError ? (
              <img 
                src={getAirlineLogoUrl(flight.airline)} 
                alt={flight.airline}
                className="airline-logo"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="airline-logo-fallback">
                {flight.airline.split(' ').map(word => word[0]).join('').substring(0, 2)}
              </div>
            )}
          </div>
          <div className="airline-details">
            <span className="airline-name">{flight.airline}</span>
            <span className="flight-number">{flight.flightNumber}</span>
            <span className="flight-class">{getFlightClass()}</span>
          </div>
        </div>
        
        <div className="price-container">
          <PriceDisplay 
            price={flight.price}
            size="large"
            style="prominent"
            showChangeIndicator={!!previousPrice}
            previousPrice={previousPrice}
          />
        </div>
      </div>

      {/* Flight route */}
      <div className="flight-route">
        <div className="departure">
          <div className="time">{formatTime(flight.departureTime)}</div>
          <div className="airport-code">{flight.origin.code}</div>
          <div className="location">
            <div className="city">{flight.origin.city}</div>
            {flight.origin.terminal && (
              <div className="terminal">Terminal {flight.origin.terminal}</div>
            )}
          </div>
        </div>

        <div className="flight-path">
          <div className="duration">{formatDuration(flight.duration)}</div>
          <div className="path-visual">
            <div className="departure-dot"></div>
            <div className="path-line">
              <div className="line"></div>
              <div className="plane-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="currentColor"/>
                </svg>
              </div>
            </div>
            <div className="arrival-dot"></div>
          </div>
          <div className="stops-info">
            <span className="stops">{getStopsText(flight.stops)}</span>
            {flight.stops > 0 && (
              <span className="stops-detail">• Layover included</span>
            )}
          </div>
        </div>

        <div className="arrival">
          <div className="time">{formatTime(flight.arrivalTime)}</div>
          <div className="airport-code">{flight.destination.code}</div>
          <div className="location">
            <div className="city">{flight.destination.city}</div>
            {flight.destination.terminal && (
              <div className="terminal">Terminal {flight.destination.terminal}</div>
            )}
          </div>
        </div>
      </div>

      {/* Quick info row */}
      <div className="flight-quick-info">
        {flight.aircraft && (
          <div className="info-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="currentColor"/>
            </svg>
            <span>{flight.aircraft}</span>
          </div>
        )}
        
        {flight.amenities && flight.amenities.length > 0 && (
          <div className="amenities-preview">
            <AmenityIcons 
              amenities={flight.amenities}
              maxVisible={3}
              size="small"
            />
          </div>
        )}
      </div>

      {/* Expandable details */}
      {isExpanded && (
        <div className="flight-details">
          <div className="details-header">
            <h4>Flight Details</h4>
          </div>
          
          <div className="details-content">
            {flight.aircraft && (
              <div className="detail-row">
                <span className="label">Aircraft Type:</span>
                <span className="value">{flight.aircraft}</span>
              </div>
            )}
            
            <div className="detail-row">
              <span className="label">Flight Duration:</span>
              <span className="value">{formatDuration(flight.duration)}</span>
            </div>

            {flight.amenities && flight.amenities.length > 0 && (
              <div className="detail-row">
                <span className="label">In-flight Amenities:</span>
                <div className="amenities-expanded">
                  <AmenityIcons 
                    amenities={flight.amenities}
                    showLabels={true}
                    layout="grid"
                    size="medium"
                  />
                </div>
              </div>
            )}

            <div className="booking-details">
              <div className="detail-row">
                <span className="label">Booking Class:</span>
                <span className="value">{getFlightClass()}</span>
              </div>
              
              <div className="detail-row">
                <span className="label">Baggage:</span>
                <span className="value">1 carry-on included</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flight-actions">
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
            'Select Flight'
          )}
        </button>
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

export default FlightCard;