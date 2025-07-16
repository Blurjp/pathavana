import React, { useState, useEffect } from 'react';
import { LegacyTravelerProfile } from '../../types/TravelerFormTypes';
import '../../styles/components/TravelerForm.css';

interface TravelerFormProps {
  traveler?: LegacyTravelerProfile | null;
  onSubmit: (data: Partial<LegacyTravelerProfile>) => void;
  onCancel: () => void;
}

const TravelerForm: React.FC<TravelerFormProps> = ({ traveler, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState<Partial<LegacyTravelerProfile>>({
    name: '',
    email: '',
    dateOfBirth: '',
    nationality: '',
    passportNumber: '',
    preferences: {
      accommodation: {
        type: 'hotel',
        rating: 3,
        amenities: [],
        location: ''
      },
      flight: {
        airline: '',
        maxStops: 1,
        preferredDepartureTime: '',
        seatPreference: ''
      },
      activities: [],
      dietary: [],
      accessibility: []
    }
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [currentTag, setCurrentTag] = useState({
    dietary: '',
    accessibility: '',
    activities: '',
    amenities: ''
  });

  useEffect(() => {
    if (traveler) {
      setFormData(traveler);
    }
  }, [traveler]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setErrors(prev => ({ ...prev, [name]: '' }));

    if (name.includes('.')) {
      const [parent, child, grandchild] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof LegacyTravelerProfile] as Record<string, any> || {}),
          [child]: grandchild ? {
            ...((prev[parent as keyof LegacyTravelerProfile] as any)?.[child] as Record<string, any> || {}),
            [grandchild]: value
          } : value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleTagInputChange = (category: string, value: string) => {
    setCurrentTag(prev => ({ ...prev, [category]: value }));
  };

  const handleAddTag = (category: 'activities' | 'dietary' | 'accessibility' | 'amenities') => {
    const value = currentTag[category].trim();
    if (!value) return;

    if (category === 'amenities') {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          accommodation: {
            ...prev.preferences!.accommodation!,
            amenities: [...(prev.preferences!.accommodation!.amenities || []), value]
          }
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          [category]: [...(prev.preferences![category] || []), value]
        }
      }));
    }

    setCurrentTag(prev => ({ ...prev, [category]: '' }));
  };

  const handleRemoveTag = (category: 'activities' | 'dietary' | 'accessibility' | 'amenities', index: number) => {
    if (category === 'amenities') {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          accommodation: {
            ...prev.preferences!.accommodation!,
            amenities: prev.preferences!.accommodation!.amenities!.filter((_, i) => i !== index)
          }
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          [category]: (prev.preferences![category] as string[]).filter((_, i) => i !== index)
        }
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (formData.dateOfBirth) {
      const birthDate = new Date(formData.dateOfBirth);
      const today = new Date();
      if (birthDate > today) {
        newErrors.dateOfBirth = 'Date of birth cannot be in the future';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="traveler-form">
      <div className="form-sections">
        {/* Personal Information Section */}
        <section className="form-section">
          <h3>Personal Information</h3>
          
          <div className="form-group">
            <label htmlFor="name">Full Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name || ''}
              onChange={handleInputChange}
              className={errors.name ? 'error' : ''}
              placeholder="Enter full name"
              required
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email || ''}
              onChange={handleInputChange}
              className={errors.email ? 'error' : ''}
              placeholder="email@example.com"
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="dateOfBirth">Date of Birth</label>
              <input
                type="date"
                id="dateOfBirth"
                name="dateOfBirth"
                value={formData.dateOfBirth || ''}
                onChange={handleInputChange}
                className={errors.dateOfBirth ? 'error' : ''}
                max={new Date().toISOString().split('T')[0]}
              />
              {errors.dateOfBirth && <span className="error-message">{errors.dateOfBirth}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="nationality">Nationality</label>
              <input
                type="text"
                id="nationality"
                name="nationality"
                value={formData.nationality || ''}
                onChange={handleInputChange}
                placeholder="e.g., United States"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="passportNumber">Passport Number</label>
            <input
              type="text"
              id="passportNumber"
              name="passportNumber"
              value={formData.passportNumber || ''}
              onChange={handleInputChange}
              placeholder="Enter passport number"
            />
            <small className="form-help">This will be stored securely and only shown partially</small>
          </div>
        </section>

        {/* Travel Preferences Section */}
        <section className="form-section">
          <h3>Travel Preferences</h3>

          {/* Dietary Restrictions */}
          <div className="form-group">
            <label>Dietary Restrictions</label>
            <div className="tag-input-container">
              <div className="tag-list">
                {formData.preferences?.dietary?.map((item, index) => (
                  <span key={index} className="tag">
                    {item}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag('dietary', index)}
                      className="tag-remove"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="tag-input">
                <input
                  type="text"
                  value={currentTag.dietary}
                  onChange={(e) => handleTagInputChange('dietary', e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag('dietary');
                    }
                  }}
                  placeholder="Add dietary restriction (e.g., Vegetarian, Gluten-free)"
                />
                <button
                  type="button"
                  onClick={() => handleAddTag('dietary')}
                  className="tag-add-btn"
                  disabled={!currentTag.dietary.trim()}
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Accessibility Needs */}
          <div className="form-group">
            <label>Accessibility Needs</label>
            <div className="tag-input-container">
              <div className="tag-list">
                {formData.preferences?.accessibility?.map((item, index) => (
                  <span key={index} className="tag">
                    {item}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag('accessibility', index)}
                      className="tag-remove"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="tag-input">
                <input
                  type="text"
                  value={currentTag.accessibility}
                  onChange={(e) => handleTagInputChange('accessibility', e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag('accessibility');
                    }
                  }}
                  placeholder="Add accessibility need (e.g., Wheelchair accessible)"
                />
                <button
                  type="button"
                  onClick={() => handleAddTag('accessibility')}
                  className="tag-add-btn"
                  disabled={!currentTag.accessibility.trim()}
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Preferred Activities */}
          <div className="form-group">
            <label>Preferred Activities</label>
            <div className="tag-input-container">
              <div className="tag-list">
                {formData.preferences?.activities?.map((item, index) => (
                  <span key={index} className="tag">
                    {item}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag('activities', index)}
                      className="tag-remove"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="tag-input">
                <input
                  type="text"
                  value={currentTag.activities}
                  onChange={(e) => handleTagInputChange('activities', e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag('activities');
                    }
                  }}
                  placeholder="Add activity (e.g., Hiking, Museums, Beach)"
                />
                <button
                  type="button"
                  onClick={() => handleAddTag('activities')}
                  className="tag-add-btn"
                  disabled={!currentTag.activities.trim()}
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Accommodation Preferences */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="accommodationType">Preferred Accommodation</label>
              <select
                id="accommodationType"
                name="preferences.accommodation.type"
                value={formData.preferences?.accommodation?.type || 'hotel'}
                onChange={handleInputChange}
              >
                <option value="hotel">Hotel</option>
                <option value="apartment">Apartment</option>
                <option value="hostel">Hostel</option>
                <option value="resort">Resort</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="accommodationRating">Minimum Rating</label>
              <select
                id="accommodationRating"
                name="preferences.accommodation.rating"
                value={formData.preferences?.accommodation?.rating || 3}
                onChange={handleInputChange}
              >
                <option value={1}>1 Star</option>
                <option value={2}>2 Stars</option>
                <option value={3}>3 Stars</option>
                <option value={4}>4 Stars</option>
                <option value={5}>5 Stars</option>
              </select>
            </div>
          </div>

          {/* Flight Preferences */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="preferredAirline">Preferred Airline</label>
              <input
                type="text"
                id="preferredAirline"
                name="preferences.flight.airline"
                value={formData.preferences?.flight?.airline || ''}
                onChange={handleInputChange}
                placeholder="e.g., United Airlines"
              />
            </div>

            <div className="form-group">
              <label htmlFor="maxStops">Maximum Stops</label>
              <select
                id="maxStops"
                name="preferences.flight.maxStops"
                value={formData.preferences?.flight?.maxStops ?? 1}
                onChange={handleInputChange}
              >
                <option value={0}>Nonstop only</option>
                <option value={1}>Up to 1 stop</option>
                <option value={2}>Up to 2 stops</option>
                <option value={3}>3+ stops OK</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="seatPreference">Seat Preference</label>
              <select
                id="seatPreference"
                name="preferences.flight.seatPreference"
                value={formData.preferences?.flight?.seatPreference || ''}
                onChange={handleInputChange}
              >
                <option value="">No preference</option>
                <option value="window">Window</option>
                <option value="aisle">Aisle</option>
                <option value="middle">Middle</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="departureTime">Preferred Departure Time</label>
              <select
                id="departureTime"
                name="preferences.flight.preferredDepartureTime"
                value={formData.preferences?.flight?.preferredDepartureTime || ''}
                onChange={handleInputChange}
              >
                <option value="">No preference</option>
                <option value="early_morning">Early Morning (5am-8am)</option>
                <option value="morning">Morning (8am-12pm)</option>
                <option value="afternoon">Afternoon (12pm-5pm)</option>
                <option value="evening">Evening (5pm-9pm)</option>
                <option value="night">Night (9pm-12am)</option>
              </select>
            </div>
          </div>
        </section>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn-primary">
          {traveler ? 'Update Traveler' : 'Add Traveler'}
        </button>
      </div>
    </form>
  );
};

export default TravelerForm;