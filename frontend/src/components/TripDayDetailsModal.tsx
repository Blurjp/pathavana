import React from 'react';
import { TripPlanItem, TripPlanDay } from '../hooks/useTripPlan';
import { FlightOption, HotelOption, ActivityOption } from '../types';
import '../styles/components/TripDayDetailsModal.css';

interface TripDayDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  dayData: TripPlanDay | null;
}

const TripDayDetailsModal: React.FC<TripDayDetailsModalProps> = ({
  isOpen,
  onClose,
  dayData
}) => {
  if (!isOpen || !dayData) return null;

  const formatPrice = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatTime = (time: string) => {
    try {
      return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return time;
    }
  };

  const renderFlightDetails = (item: TripPlanItem) => {
    const flight = item.data as FlightOption;
    return (
      <div className="trip-detail-card flight-card">
        <div className="detail-header">
          <span className="detail-icon">✈️</span>
          <div className="detail-title">
            <h4>{flight.airline} {flight.flightNumber}</h4>
            <p className="detail-subtitle">Flight Details</p>
          </div>
          <div className="detail-price">
            {flight.price && formatPrice(flight.price.amount, flight.price.currency)}
          </div>
        </div>
        
        <div className="flight-route-details">
          <div className="airport-section">
            <div className="airport-code">{flight.origin.code}</div>
            <div className="airport-name">{flight.origin.name}</div>
            <div className="flight-time">{formatTime(flight.departureTime)}</div>
          </div>
          
          <div className="flight-arrow">
            <div className="arrow-line"></div>
            <div className="flight-duration">{flight.duration}</div>
            <div className="arrow-head">→</div>
          </div>
          
          <div className="airport-section">
            <div className="airport-code">{flight.destination.code}</div>
            <div className="airport-name">{flight.destination.name}</div>
            <div className="flight-time">{formatTime(flight.arrivalTime)}</div>
          </div>
        </div>

        {flight.amenities && flight.amenities.length > 0 && (
          <div className="flight-amenities">
            <h5>Amenities</h5>
            <div className="amenities-list">
              {flight.amenities.map((amenity, index) => (
                <span key={index} className="amenity-tag">{amenity}</span>
              ))}
            </div>
          </div>
        )}

        {item.notes && (
          <div className="item-notes">
            <h5>Notes</h5>
            <p>{item.notes}</p>
          </div>
        )}
      </div>
    );
  };

  const renderHotelDetails = (item: TripPlanItem) => {
    const hotel = item.data as HotelOption;
    return (
      <div className="trip-detail-card hotel-card">
        <div className="detail-header">
          <span className="detail-icon">🏨</span>
          <div className="detail-title">
            <h4>{hotel.name}</h4>
            <p className="detail-subtitle">
              {hotel.rating && '⭐'.repeat(Math.floor(hotel.rating))} Hotel
            </p>
          </div>
          <div className="detail-price">
            {hotel.price && formatPrice(hotel.price.amount, hotel.price.currency)}
            <span className="price-period">per night</span>
          </div>
        </div>

        <div className="hotel-details">
          {hotel.location && (
            <div className="hotel-location">
              <span className="location-icon">📍</span>
              <span>{hotel.location.address}</span>
            </div>
          )}

          {hotel.amenities && hotel.amenities.length > 0 && (
            <div className="hotel-amenities">
              <h5>Amenities</h5>
              <div className="amenities-grid">
                {hotel.amenities.map((amenity, index) => (
                  <div key={index} className="amenity-item">
                    <span className="amenity-icon">
                      {amenity.includes('WiFi') ? '📶' :
                       amenity.includes('Pool') ? '🏊' :
                       amenity.includes('Gym') ? '💪' :
                       amenity.includes('Parking') ? '🚗' :
                       amenity.includes('Breakfast') ? '🍳' :
                       amenity.includes('Restaurant') ? '🍽️' : '✓'}
                    </span>
                    <span>{amenity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {hotel.images && hotel.images.length > 0 && (
            <div className="hotel-images">
              <div className="image-gallery">
                {hotel.images.slice(0, 3).map((image, index) => (
                  <img 
                    key={index} 
                    src={image} 
                    alt={`${hotel.name} view ${index + 1}`}
                    className="hotel-image"
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {item.notes && (
          <div className="item-notes">
            <h5>Notes</h5>
            <p>{item.notes}</p>
          </div>
        )}
      </div>
    );
  };

  const renderActivityDetails = (item: TripPlanItem) => {
    const activity = item.data as ActivityOption;
    return (
      <div className="trip-detail-card activity-card">
        <div className="detail-header">
          <span className="detail-icon">🎫</span>
          <div className="detail-title">
            <h4>{activity.name}</h4>
            <p className="detail-subtitle">Activity</p>
          </div>
          <div className="detail-price">
            {activity.price && formatPrice(activity.price.amount, activity.price.currency)}
          </div>
        </div>

        <div className="activity-details">
          {activity.description && (
            <div className="activity-description">
              <p>{activity.description}</p>
            </div>
          )}

          {activity.duration && (
            <div className="activity-duration">
              <span className="duration-icon">⏱️</span>
              <span>Duration: {activity.duration}</span>
            </div>
          )}

          {activity.location && (
            <div className="activity-location">
              <span className="location-icon">📍</span>
              <span>{activity.location.address || activity.location.city}</span>
            </div>
          )}
        </div>

        {item.notes && (
          <div className="item-notes">
            <h5>Notes</h5>
            <p>{item.notes}</p>
          </div>
        )}
      </div>
    );
  };

  const renderItemDetails = (item: TripPlanItem) => {
    switch (item.type) {
      case 'flight':
        return renderFlightDetails(item);
      case 'hotel':
        return renderHotelDetails(item);
      case 'activity':
        return renderActivityDetails(item);
      default:
        return (
          <div className="trip-detail-card generic-card">
            <div className="detail-header">
              <span className="detail-icon">📍</span>
              <div className="detail-title">
                <h4>{item.type}</h4>
              </div>
            </div>
            {item.notes && (
              <div className="item-notes">
                <p>{item.notes}</p>
              </div>
            )}
          </div>
        );
    }
  };

  const flightItems = dayData.items.filter(item => item.type === 'flight');
  const hotelItems = dayData.items.filter(item => item.type === 'hotel');
  const activityItems = dayData.items.filter(item => item.type === 'activity');
  const otherItems = dayData.items.filter(item => !['flight', 'hotel', 'activity'].includes(item.type));

  return (
    <div className="trip-day-details-modal-overlay" onClick={onClose}>
      <div className="trip-day-details-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <h3>Day {dayData.day} Details</h3>
            <p className="modal-date">{new Date(dayData.date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          {flightItems.length > 0 && (
            <div className="details-section">
              <h4 className="section-title">✈️ Flights</h4>
              {flightItems.map(item => (
                <div key={item.id}>{renderItemDetails(item)}</div>
              ))}
            </div>
          )}

          {hotelItems.length > 0 && (
            <div className="details-section">
              <h4 className="section-title">🏨 Hotels</h4>
              {hotelItems.map(item => (
                <div key={item.id}>{renderItemDetails(item)}</div>
              ))}
            </div>
          )}

          {activityItems.length > 0 && (
            <div className="details-section">
              <h4 className="section-title">🎫 Activities</h4>
              {activityItems.map(item => (
                <div key={item.id}>{renderItemDetails(item)}</div>
              ))}
            </div>
          )}

          {otherItems.length > 0 && (
            <div className="details-section">
              <h4 className="section-title">📍 Other Items</h4>
              {otherItems.map(item => (
                <div key={item.id}>{renderItemDetails(item)}</div>
              ))}
            </div>
          )}

          {dayData.items.length === 0 && (
            <div className="empty-day">
              <p>No items planned for this day yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TripDayDetailsModal;