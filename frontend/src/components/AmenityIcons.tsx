import React from 'react';
import './AmenityIcons.css';

interface AmenityIconsProps {
  amenities: string[];
  maxVisible?: number;
  size?: 'small' | 'medium' | 'large';
  showLabels?: boolean;
  layout?: 'horizontal' | 'grid';
  className?: string;
}

// Icon mapping for common amenities
const amenityIconMap: Record<string, { icon: string; label: string }> = {
  // Hotel amenities
  'wifi': { icon: '📶', label: 'WiFi' },
  'free wifi': { icon: '📶', label: 'Free WiFi' },
  'parking': { icon: '🅿️', label: 'Parking' },
  'pool': { icon: '🏊', label: 'Pool' },
  'gym': { icon: '🏋️', label: 'Gym' },
  'spa': { icon: '🧘', label: 'Spa' },
  'restaurant': { icon: '🍽️', label: 'Restaurant' },
  'bar': { icon: '🍸', label: 'Bar' },
  'room service': { icon: '🛎️', label: 'Room Service' },
  'concierge': { icon: '🛎️', label: 'Concierge' },
  'laundry': { icon: '👕', label: 'Laundry' },
  'business center': { icon: '💼', label: 'Business Center' },
  'meeting rooms': { icon: '🏢', label: 'Meeting Rooms' },
  'pet friendly': { icon: '🐕', label: 'Pet Friendly' },
  'air conditioning': { icon: '❄️', label: 'AC' },
  'heating': { icon: '🔥', label: 'Heating' },
  'kitchen': { icon: '🍳', label: 'Kitchen' },
  'balcony': { icon: '🏡', label: 'Balcony' },
  'terrace': { icon: '🏡', label: 'Terrace' },
  'beach access': { icon: '🏖️', label: 'Beach Access' },
  'airport shuttle': { icon: '🚐', label: 'Airport Shuttle' },
  
  // Flight amenities
  'entertainment': { icon: '📺', label: 'Entertainment' },
  'meals': { icon: '🍽️', label: 'Meals' },
  'drinks': { icon: '🥤', label: 'Drinks' },
  'power outlets': { icon: '🔌', label: 'Power' },
  'usb': { icon: '🔌', label: 'USB' },
  'wifi onboard': { icon: '📶', label: 'WiFi' },
  'extra legroom': { icon: '📐', label: 'Extra Legroom' },
  'priority boarding': { icon: '✈️', label: 'Priority Boarding' },
  'baggage': { icon: '🎒', label: 'Baggage' },
  'checked bag': { icon: '🧳', label: 'Checked Bag' },
  'carry on': { icon: '🎒', label: 'Carry On' },
  
  // Activity amenities
  'guide': { icon: '👤', label: 'Guide' },
  'transport included': { icon: '🚌', label: 'Transport' },
  'meals included': { icon: '🍽️', label: 'Meals' },
  'equipment provided': { icon: '⚙️', label: 'Equipment' },
  'small group': { icon: '👥', label: 'Small Group' },
  'pickup included': { icon: '🚐', label: 'Pickup' },
  'entrance fees': { icon: '🎫', label: 'Entrance Fees' },
  'insurance': { icon: '🛡️', label: 'Insurance' },
  'photos': { icon: '📸', label: 'Photos' },
  'certificate': { icon: '🏆', label: 'Certificate' },
};

const getAmenityIcon = (amenity: string): { icon: string; label: string } => {
  const normalizedAmenity = amenity.toLowerCase().trim();
  
  // Direct match
  if (amenityIconMap[normalizedAmenity]) {
    return amenityIconMap[normalizedAmenity];
  }
  
  // Partial match for more complex amenity names
  for (const [key, value] of Object.entries(amenityIconMap)) {
    if (normalizedAmenity.includes(key) || key.includes(normalizedAmenity)) {
      return value;
    }
  }
  
  // Default icon for unknown amenities
  return { icon: '•', label: amenity };
};

const AmenityIcons: React.FC<AmenityIconsProps> = ({
  amenities,
  maxVisible = 6,
  size = 'medium',
  showLabels = false,
  layout = 'horizontal',
  className = ''
}) => {
  const visibleAmenities = amenities.slice(0, maxVisible);
  const hiddenCount = Math.max(0, amenities.length - maxVisible);

  return (
    <div className={`amenity-icons ${size} ${layout} ${showLabels ? 'with-labels' : ''} ${className}`}>
      <div className="amenities-list">
        {visibleAmenities.map((amenity, index) => {
          const { icon, label } = getAmenityIcon(amenity);
          
          return (
            <div
              key={index}
              className="amenity-item"
              title={showLabels ? undefined : label}
            >
              <span className="amenity-icon" role="img" aria-label={label}>
                {icon}
              </span>
              {showLabels && (
                <span className="amenity-label">{label}</span>
              )}
            </div>
          );
        })}
        
        {hiddenCount > 0 && (
          <div className="amenity-item more-count" title={`+${hiddenCount} more amenities`}>
            <span className="amenity-icon">+{hiddenCount}</span>
            {showLabels && (
              <span className="amenity-label">more</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AmenityIcons;