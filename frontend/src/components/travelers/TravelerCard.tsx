import React from 'react';
import { TravelerProfile } from '../../types';
import { formatDate } from '../../utils/dateHelpers';
import '../../styles/components/TravelerCard.css';

interface TravelerCardProps {
  traveler: TravelerProfile;
  onEdit: () => void;
  onDelete: () => void;
}

const TravelerCard: React.FC<TravelerCardProps> = ({ traveler, onEdit, onDelete }) => {
  const fullName = traveler.full_name || `${traveler.first_name} ${traveler.last_name}`.trim();
  
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  };

  return (
    <div className="traveler-card">
      <div className="traveler-card-header">
        <div className="traveler-avatar">
          {getInitials(fullName)}
        </div>
        <div className="traveler-info">
          <h3 className="traveler-name">{fullName}</h3>
          {traveler.email && (
            <p className="traveler-email">{traveler.email}</p>
          )}
        </div>
        <div className="traveler-actions">
          <button
            onClick={onEdit}
            className="action-btn edit-btn"
            aria-label="Edit traveler"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="action-btn delete-btn"
            aria-label="Delete traveler"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
              <path fillRule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
            </svg>
          </button>
        </div>
      </div>

      <div className="traveler-details">
        {traveler.date_of_birth && (
          <div className="detail-row">
            <span className="detail-label">Age</span>
            <span className="detail-value">{getAge(traveler.date_of_birth)} years</span>
          </div>
        )}

        {traveler.nationality && (
          <div className="detail-row">
            <span className="detail-label">Nationality</span>
            <span className="detail-value">{traveler.nationality}</span>
          </div>
        )}

        {/* Passport would come from documents in the new schema */}

        {/* Show dietary restrictions from root level or preferences */}
        {(traveler.dietary_restrictions && traveler.dietary_restrictions.length > 0) && (
          <div className="detail-section">
            <span className="detail-label">Dietary Restrictions</span>
            <div className="tag-list">
              {traveler.dietary_restrictions.map((item, index) => (
                <span key={index} className="tag dietary-tag">{item}</span>
              ))}
            </div>
          </div>
        )}

        {/* Show accessibility needs from root level or preferences */}
        {(traveler.accessibility_needs && traveler.accessibility_needs.length > 0) && (
          <div className="detail-section">
            <span className="detail-label">Accessibility Needs</span>
            <div className="tag-list">
              {traveler.accessibility_needs.map((item, index) => (
                <span key={index} className="tag accessibility-tag">{item}</span>
              ))}
            </div>
          </div>
        )}

        {traveler.preferences && (
          <>

            {traveler.preferences.flight && (
              <div className="preferences-summary">
                {traveler.preferences.flight.seatPreference && (
                  <span className="pref-item">
                    ✈️ {traveler.preferences.flight.seatPreference} seat
                  </span>
                )}
                {traveler.preferences.flight.preferredDepartureTime && (
                  <span className="pref-item">
                    🕐 {traveler.preferences.flight.preferredDepartureTime} departure
                  </span>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TravelerCard;