import React, { useState, useEffect } from 'react';
import { TravelerProfile } from '../types';
import { travelApi } from '../services/travelApi';
import { formatDate } from '../utils/dateHelpers';
import { handleApiError } from '../utils/errorHandler';

const Travelers: React.FC = () => {
  const [travelers, setTravelers] = useState<TravelerProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTraveler, setEditingTraveler] = useState<TravelerProfile | null>(null);

  const [formData, setFormData] = useState<Partial<TravelerProfile>>({
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

  useEffect(() => {
    loadTravelers();
  }, []);

  const loadTravelers = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await travelApi.getTravelers();
      if (response.success && response.data) {
        setTravelers(response.data);
      } else {
        throw new Error(response.error || 'Failed to load travelers');
      }
    } catch (err: any) {
      setError(handleApiError(err, 'travelers'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    if (name.includes('.')) {
      const [parent, child, grandchild] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof TravelerProfile] as Record<string, any> || {}),
          [child]: grandchild ? {
            ...((prev[parent as keyof TravelerProfile] as any)?.[child] as Record<string, any> || {}),
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

  const handleArrayInputChange = (
    category: 'activities' | 'dietary' | 'accessibility' | 'amenities',
    value: string
  ) => {
    if (!value.trim()) return;

    if (category === 'amenities') {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          accommodation: {
            ...prev.preferences!.accommodation!,
            amenities: [
              ...prev.preferences!.accommodation!.amenities!,
              value.trim()
            ]
          }
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        preferences: {
          ...prev.preferences!,
          [category]: [
            ...prev.preferences![category as keyof typeof prev.preferences]!,
            value.trim()
          ]
        }
      }));
    }
  };

  const handleArrayItemRemove = (
    category: 'activities' | 'dietary' | 'accessibility' | 'amenities',
    index: number
  ) => {
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
          [category]: (prev.preferences![category as keyof typeof prev.preferences]! as string[]).filter((_, i) => i !== index)
        }
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      let response: any;
      if (editingTraveler) {
        response = await travelApi.updateTraveler(editingTraveler.id, formData);
      } else {
        response = await travelApi.createTraveler(formData);
      }

      if (response.success && response.data) {
        if (editingTraveler) {
          setTravelers(prev => prev.map(t => 
            t.id === editingTraveler.id ? response.data! : t
          ));
        } else {
          setTravelers(prev => [...prev, response.data!]);
        }
        
        resetForm();
      } else {
        throw new Error(response.error || 'Failed to save traveler');
      }
    } catch (err: any) {
      setError(handleApiError(err, 'save_traveler'));
    }
  };

  const handleEdit = (traveler: TravelerProfile) => {
    setFormData(traveler);
    setEditingTraveler(traveler);
    setShowAddForm(true);
  };

  const handleDelete = async (travelerId: string) => {
    if (!window.confirm('Are you sure you want to delete this traveler profile?')) {
      return;
    }

    try {
      const response = await travelApi.deleteTraveler(travelerId);
      if (response.success) {
        setTravelers(prev => prev.filter(t => t.id !== travelerId));
      } else {
        throw new Error(response.error || 'Failed to delete traveler');
      }
    } catch (err: any) {
      setError(handleApiError(err, 'delete_traveler'));
    }
  };

  const resetForm = () => {
    setFormData({
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
    setEditingTraveler(null);
    setShowAddForm(false);
    setError(null);
  };

  const renderTravelerCard = (traveler: TravelerProfile) => (
    <div key={traveler.id} className="traveler-card">
      <div className="traveler-header">
        <div className="traveler-info">
          <h3>{traveler.name}</h3>
          {traveler.email && <p className="email">{traveler.email}</p>}
        </div>
        <div className="traveler-actions">
          <button
            onClick={() => handleEdit(traveler)}
            className="btn-secondary"
          >
            Edit
          </button>
          <button
            onClick={() => handleDelete(traveler.id)}
            className="btn-danger"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="traveler-details">
        {traveler.dateOfBirth && (
          <div className="detail-item">
            <span className="label">Date of Birth:</span>
            <span className="value">{formatDate(traveler.dateOfBirth)}</span>
          </div>
        )}

        {traveler.nationality && (
          <div className="detail-item">
            <span className="label">Nationality:</span>
            <span className="value">{traveler.nationality}</span>
          </div>
        )}

        {traveler.passportNumber && (
          <div className="detail-item">
            <span className="label">Passport:</span>
            <span className="value">***{traveler.passportNumber.slice(-4)}</span>
          </div>
        )}

        {traveler.preferences?.dietary && traveler.preferences.dietary.length > 0 && (
          <div className="detail-item">
            <span className="label">Dietary:</span>
            <div className="tags">
              {traveler.preferences.dietary.map((item, index) => (
                <span key={index} className="tag">{item}</span>
              ))}
            </div>
          </div>
        )}

        {traveler.preferences?.accessibility && traveler.preferences.accessibility.length > 0 && (
          <div className="detail-item">
            <span className="label">Accessibility:</span>
            <div className="tags">
              {traveler.preferences.accessibility.map((item, index) => (
                <span key={index} className="tag">{item}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="travelers-page">
      <div className="page-header">
        <h1>Traveler Profiles</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn-primary"
        >
          Add Traveler
        </button>
      </div>

      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
        </div>
      )}

      {/* Add/Edit Form Modal */}
      {showAddForm && (
        <div className="modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) resetForm();
        }}>
          <div className="modal-content">
            <div className="modal-header">
              <h2>{editingTraveler ? 'Edit Traveler' : 'Add New Traveler'}</h2>
              <button onClick={resetForm} className="close-button">×</button>
            </div>

            <form onSubmit={handleSubmit} className="traveler-form">
              {/* Personal Information */}
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
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email || ''}
                    onChange={handleInputChange}
                  />
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
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="nationality">Nationality</label>
                    <input
                      type="text"
                      id="nationality"
                      name="nationality"
                      value={formData.nationality || ''}
                      onChange={handleInputChange}
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
                  />
                </div>
              </section>

              {/* Travel Preferences */}
              <section className="form-section">
                <h3>Travel Preferences</h3>

                {/* Dietary Restrictions */}
                <div className="form-group">
                  <label>Dietary Restrictions</label>
                  <div className="array-input">
                    <div className="array-items">
                      {formData.preferences?.dietary?.map((item, index) => (
                        <span key={index} className="array-item">
                          {item}
                          <button
                            type="button"
                            onClick={() => handleArrayItemRemove('dietary', index)}
                            className="remove-item"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      placeholder="Add dietary restriction..."
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleArrayInputChange('dietary', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                  </div>
                </div>

                {/* Accessibility Needs */}
                <div className="form-group">
                  <label>Accessibility Needs</label>
                  <div className="array-input">
                    <div className="array-items">
                      {formData.preferences?.accessibility?.map((item, index) => (
                        <span key={index} className="array-item">
                          {item}
                          <button
                            type="button"
                            onClick={() => handleArrayItemRemove('accessibility', index)}
                            className="remove-item"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      placeholder="Add accessibility need..."
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleArrayInputChange('accessibility', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
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
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="maxStops">Max Stops</label>
                    <select
                      id="maxStops"
                      name="preferences.flight.maxStops"
                      value={formData.preferences?.flight?.maxStops || 1}
                      onChange={handleInputChange}
                    >
                      <option value={0}>Nonstop</option>
                      <option value={1}>1 Stop</option>
                      <option value={2}>2 Stops</option>
                      <option value={3}>3+ Stops</option>
                    </select>
                  </div>
                </div>
              </section>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingTraveler ? 'Update Traveler' : 'Add Traveler'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Travelers List */}
      <div className="travelers-content">
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner large" />
            <p>Loading travelers...</p>
          </div>
        ) : travelers.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👥</div>
            <h3>No traveler profiles yet</h3>
            <p>Add traveler profiles to save their preferences and information for future trips</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="btn-primary"
            >
              Add Your First Traveler
            </button>
          </div>
        ) : (
          <div className="travelers-grid">
            {travelers.map(renderTravelerCard)}
          </div>
        )}
      </div>
    </div>
  );
};

export default Travelers;