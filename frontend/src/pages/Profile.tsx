import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { User, UserPreferences } from '../types';
import { handleApiError } from '../utils/errorHandler';
import '../styles/pages/Profile.css';

const Profile: React.FC = () => {
  const { user, updateUser, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<Partial<User>>({
    full_name: '',
    email: '',
    preferences: {
      currency: 'USD',
      language: 'en',
      timezone: 'UTC',
      notifications: {
        email: true,
        push: false,
        tripUpdates: true,
        priceAlerts: true,
        marketing: false
      },
      privacy: {
        shareTrips: false,
        publicProfile: false,
        dataCollection: true
      },
      travel: {
        defaultTravelClass: 'economy',
        preferredAirlines: [],
        preferredHotelBrands: [],
        dietaryRestrictions: [],
        accessibilityNeeds: [],
        loyaltyPrograms: []
      }
    }
  });

  useEffect(() => {
    if (user) {
      setFormData(user);
    }
  }, [user]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;

    if (name.includes('.')) {
      const [parent, child, grandchild] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof User] as Record<string, any> || {}),
          [child]: grandchild ? {
            ...((prev[parent as keyof User] as any)?.[child] as Record<string, any> || {}),
            [grandchild]: type === 'checkbox' ? checked : value
          } : type === 'checkbox' ? checked : value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleArrayInputChange = (
    category: 'preferredAirlines' | 'preferredHotelBrands' | 'dietaryRestrictions' | 'accessibilityNeeds',
    value: string
  ) => {
    if (!value.trim()) return;

    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences!,
        travel: {
          ...prev.preferences!.travel!,
          [category]: [
            ...prev.preferences!.travel![category],
            value.trim()
          ]
        }
      }
    }));
  };

  const handleArrayItemRemove = (
    category: 'preferredAirlines' | 'preferredHotelBrands' | 'dietaryRestrictions' | 'accessibilityNeeds',
    index: number
  ) => {
    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences!,
        travel: {
          ...prev.preferences!.travel!,
          [category]: prev.preferences!.travel![category].filter((_, i) => i !== index)
        }
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const success = await updateUser(formData);
      
      if (success) {
        setSuccess('Profile updated successfully!');
        setIsEditing(false);
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (err: any) {
      setError(handleApiError(err, 'profile_update'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData(user);
    }
    setIsEditing(false);
    setError(null);
  };

  if (authLoading) {
    return (
      <div className="profile-page">
        <div className="loading-state">
          <div className="loading-spinner large" />
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-page">
        <div className="error-state">
          <h2>Please log in to view your profile</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="page-header">
        <h1>Profile Settings</h1>
        <div className="header-actions">
          <button
            onClick={() => navigate('/profile/settings')}
            className="btn-secondary"
          >
            Advanced Settings
          </button>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="btn-primary"
            >
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {success && (
        <div className="success-message">
          <div className="success-icon">✅</div>
          <p>{success}</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="profile-form">
        {/* Personal Information */}
        <section className="form-section">
          <h2>Personal Information</h2>
          
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name || ''}
              onChange={handleInputChange}
              disabled={!isEditing}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email || ''}
              onChange={handleInputChange}
              disabled={!isEditing}
              required
            />
          </div>
        </section>

        {/* General Preferences */}
        <section className="form-section">
          <h2>General Preferences</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="currency">Currency</label>
              <select
                id="currency"
                name="preferences.currency"
                value={formData.preferences?.currency || 'USD'}
                onChange={handleInputChange}
                disabled={!isEditing}
              >
                <option value="USD">USD - US Dollar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="GBP">GBP - British Pound</option>
                <option value="JPY">JPY - Japanese Yen</option>
                <option value="CAD">CAD - Canadian Dollar</option>
                <option value="AUD">AUD - Australian Dollar</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                name="preferences.language"
                value={formData.preferences?.language || 'en'}
                onChange={handleInputChange}
                disabled={!isEditing}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="ja">Japanese</option>
              </select>
            </div>
          </div>
        </section>

        {/* Travel Preferences */}
        <section className="form-section">
          <h2>Travel Preferences</h2>
          
          <div className="form-group">
            <label htmlFor="defaultTravelClass">Default Travel Class</label>
            <select
              id="defaultTravelClass"
              name="preferences.travel.defaultTravelClass"
              value={formData.preferences?.travel?.defaultTravelClass || 'economy'}
              onChange={handleInputChange}
              disabled={!isEditing}
            >
              <option value="economy">Economy</option>
              <option value="premium_economy">Premium Economy</option>
              <option value="business">Business</option>
              <option value="first">First Class</option>
            </select>
          </div>

          {/* Preferred Airlines */}
          <div className="form-group">
            <label>Preferred Airlines</label>
            <div className="array-input">
              <div className="array-items">
                {formData.preferences?.travel?.preferredAirlines?.map((airline, index) => (
                  <span key={index} className="array-item">
                    {airline}
                    {isEditing && (
                      <button
                        type="button"
                        onClick={() => handleArrayItemRemove('preferredAirlines', index)}
                        className="remove-item"
                      >
                        ×
                      </button>
                    )}
                  </span>
                ))}
              </div>
              {isEditing && (
                <input
                  type="text"
                  placeholder="Add airline..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleArrayInputChange('preferredAirlines', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
              )}
            </div>
          </div>

          {/* Dietary Restrictions */}
          <div className="form-group">
            <label>Dietary Restrictions</label>
            <div className="array-input">
              <div className="array-items">
                {formData.preferences?.travel?.dietaryRestrictions?.map((restriction, index) => (
                  <span key={index} className="array-item">
                    {restriction}
                    {isEditing && (
                      <button
                        type="button"
                        onClick={() => handleArrayItemRemove('dietaryRestrictions', index)}
                        className="remove-item"
                      >
                        ×
                      </button>
                    )}
                  </span>
                ))}
              </div>
              {isEditing && (
                <input
                  type="text"
                  placeholder="Add dietary restriction..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleArrayInputChange('dietaryRestrictions', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
              )}
            </div>
          </div>
        </section>

        {/* Notification Settings */}
        <section className="form-section">
          <h2>Notifications</h2>
          
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.notifications.email"
                checked={formData.preferences?.notifications?.email || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Email notifications
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.notifications.tripUpdates"
                checked={formData.preferences?.notifications?.tripUpdates || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Trip updates
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.notifications.priceAlerts"
                checked={formData.preferences?.notifications?.priceAlerts || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Price alerts
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.notifications.marketing"
                checked={formData.preferences?.notifications?.marketing || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Marketing emails
            </label>
          </div>
        </section>

        {/* Privacy Settings */}
        <section className="form-section">
          <h2>Privacy</h2>
          
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.privacy.shareTrips"
                checked={formData.preferences?.privacy?.shareTrips || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Allow sharing trips with other users
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.privacy.publicProfile"
                checked={formData.preferences?.privacy?.publicProfile || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Make profile public
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="preferences.privacy.dataCollection"
                checked={formData.preferences?.privacy?.dataCollection || false}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
              Allow data collection for improving service
            </label>
          </div>
        </section>

        {/* Form Actions */}
        {isEditing && (
          <div className="form-actions">
            <button
              type="button"
              onClick={handleCancel}
              className="btn-secondary"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default Profile;