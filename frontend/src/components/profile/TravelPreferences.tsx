import React, { useState, useEffect } from 'react';
import { Save, Plus, X, Plane, Hotel, DollarSign, Users, Clock, Activity } from 'lucide-react';
import '../../styles/components/profile/TravelPreferences.css';

interface TravelPreferencesProps {
  preferences: any;
  onUpdate: (preferences: any) => Promise<void>;
  loading: boolean;
  error: string | null;
}

interface Preferences {
  travelStyle: string[];
  budget: string;
  accommodationType: string[];
  interests: string[];
  dietaryRestrictions: string[];
  accessibility: string[];
  travelPace: string;
  groupSize: string;
  preferredAirlines: string[];
  preferredHotelChains: string[];
}

const TravelPreferences: React.FC<TravelPreferencesProps> = ({
  preferences,
  onUpdate,
  loading,
  error,
}) => {
  const [formData, setFormData] = useState<Preferences>({
    travelStyle: [],
    budget: 'moderate',
    accommodationType: [],
    interests: [],
    dietaryRestrictions: [],
    accessibility: [],
    travelPace: 'moderate',
    groupSize: 'couple',
    preferredAirlines: [],
    preferredHotelChains: [],
  });

  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [newInterest, setNewInterest] = useState('');
  const [newAirline, setNewAirline] = useState('');
  const [newHotelChain, setNewHotelChain] = useState('');

  useEffect(() => {
    if (preferences) {
      setFormData({
        travelStyle: preferences.travelStyle || [],
        budget: preferences.budget || 'moderate',
        accommodationType: preferences.accommodationType || [],
        interests: preferences.interests || [],
        dietaryRestrictions: preferences.dietaryRestrictions || [],
        accessibility: preferences.accessibility || [],
        travelPace: preferences.travelPace || 'moderate',
        groupSize: preferences.groupSize || 'couple',
        preferredAirlines: preferences.preferredAirlines || [],
        preferredHotelChains: preferences.preferredHotelChains || [],
      });
    }
  }, [preferences]);

  const travelStyles = [
    { value: 'adventure', label: 'Adventure', icon: '🏔️' },
    { value: 'relaxation', label: 'Relaxation', icon: '🏖️' },
    { value: 'cultural', label: 'Cultural', icon: '🏛️' },
    { value: 'luxury', label: 'Luxury', icon: '💎' },
    { value: 'budget', label: 'Budget', icon: '💰' },
    { value: 'eco', label: 'Eco-friendly', icon: '🌿' },
    { value: 'family', label: 'Family-friendly', icon: '👨‍👩‍👧‍👦' },
    { value: 'romantic', label: 'Romantic', icon: '💑' },
  ];

  const accommodationTypes = [
    { value: 'hotel', label: 'Hotels' },
    { value: 'resort', label: 'Resorts' },
    { value: 'airbnb', label: 'Vacation Rentals' },
    { value: 'hostel', label: 'Hostels' },
    { value: 'boutique', label: 'Boutique Hotels' },
    { value: 'bnb', label: 'Bed & Breakfast' },
  ];

  const dietaryOptions = [
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'gluten-free', label: 'Gluten-free' },
    { value: 'halal', label: 'Halal' },
    { value: 'kosher', label: 'Kosher' },
    { value: 'lactose-free', label: 'Lactose-free' },
    { value: 'nut-allergy', label: 'Nut Allergies' },
  ];

  const accessibilityOptions = [
    { value: 'wheelchair', label: 'Wheelchair Accessible' },
    { value: 'mobility', label: 'Limited Mobility' },
    { value: 'visual', label: 'Visual Assistance' },
    { value: 'hearing', label: 'Hearing Assistance' },
  ];

  const handleMultiSelect = (category: keyof Preferences, value: string) => {
    setFormData(prev => {
      const currentValues = prev[category] as string[];
      const newValues = currentValues.includes(value)
        ? currentValues.filter(v => v !== value)
        : [...currentValues, value];
      
      return { ...prev, [category]: newValues };
    });
    setIsEditing(true);
  };

  const handleSingleSelect = (category: keyof Preferences, value: string) => {
    setFormData(prev => ({ ...prev, [category]: value }));
    setIsEditing(true);
  };

  const handleAddItem = (category: keyof Preferences, value: string, setter: (value: string) => void) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [category]: [...(prev[category] as string[]), value.trim()]
      }));
      setter('');
      setIsEditing(true);
    }
  };

  const handleRemoveItem = (category: keyof Preferences, value: string) => {
    setFormData(prev => ({
      ...prev,
      [category]: (prev[category] as string[]).filter(v => v !== value)
    }));
    setIsEditing(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');
    
    try {
      await onUpdate(formData);
      setSaveStatus('saved');
      setIsEditing(false);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err) {
      setSaveStatus('idle');
      console.error('Failed to update preferences:', err);
    }
  };

  return (
    <div className="travel-preferences">
      <form onSubmit={handleSubmit}>
        <div className="preferences-header">
          <h2>Travel Preferences</h2>
          {isEditing && (
            <button
              type="submit"
              className="save-button"
              disabled={loading || saveStatus === 'saving'}
            >
              <Save size={18} />
              {saveStatus === 'saving' ? 'Saving...' : 
               saveStatus === 'saved' ? 'Saved!' : 'Save Changes'}
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="preference-section">
          <h3>Travel Style</h3>
          <p className="section-description">Select all that apply to your travel preferences</p>
          <div className="style-grid">
            {travelStyles.map(style => (
              <label
                key={style.value}
                className={`style-option ${formData.travelStyle.includes(style.value) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={formData.travelStyle.includes(style.value)}
                  onChange={() => handleMultiSelect('travelStyle', style.value)}
                />
                <span className="style-icon">{style.icon}</span>
                <span className="style-label">{style.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <DollarSign size={20} />
            Budget Range
          </h3>
          <div className="budget-options">
            <label className={`budget-option ${formData.budget === 'budget' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="budget"
                value="budget"
                checked={formData.budget === 'budget'}
                onChange={(e) => handleSingleSelect('budget', e.target.value)}
              />
              <span>Budget ($)</span>
            </label>
            <label className={`budget-option ${formData.budget === 'moderate' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="budget"
                value="moderate"
                checked={formData.budget === 'moderate'}
                onChange={(e) => handleSingleSelect('budget', e.target.value)}
              />
              <span>Moderate ($$)</span>
            </label>
            <label className={`budget-option ${formData.budget === 'premium' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="budget"
                value="premium"
                checked={formData.budget === 'premium'}
                onChange={(e) => handleSingleSelect('budget', e.target.value)}
              />
              <span>Premium ($$$)</span>
            </label>
            <label className={`budget-option ${formData.budget === 'luxury' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="budget"
                value="luxury"
                checked={formData.budget === 'luxury'}
                onChange={(e) => handleSingleSelect('budget', e.target.value)}
              />
              <span>Luxury ($$$$)</span>
            </label>
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Hotel size={20} />
            Accommodation Preferences
          </h3>
          <div className="checkbox-grid">
            {accommodationTypes.map(type => (
              <label key={type.value} className="checkbox-option">
                <input
                  type="checkbox"
                  checked={formData.accommodationType.includes(type.value)}
                  onChange={() => handleMultiSelect('accommodationType', type.value)}
                />
                <span>{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Activity size={20} />
            Interests
          </h3>
          <div className="tag-input-container">
            <div className="tag-list">
              {formData.interests.map(interest => (
                <span key={interest} className="tag">
                  {interest}
                  <button
                    type="button"
                    onClick={() => handleRemoveItem('interests', interest)}
                    className="tag-remove"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
            <div className="tag-input">
              <input
                type="text"
                value={newInterest}
                onChange={(e) => setNewInterest(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddItem('interests', newInterest, setNewInterest);
                  }
                }}
                placeholder="Add an interest (e.g., Photography, Hiking)"
              />
              <button
                type="button"
                onClick={() => handleAddItem('interests', newInterest, setNewInterest)}
                className="add-button"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>
        </div>

        <div className="preference-section">
          <h3>Dietary Restrictions</h3>
          <div className="checkbox-grid">
            {dietaryOptions.map(option => (
              <label key={option.value} className="checkbox-option">
                <input
                  type="checkbox"
                  checked={formData.dietaryRestrictions.includes(option.value)}
                  onChange={() => handleMultiSelect('dietaryRestrictions', option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>Accessibility Needs</h3>
          <div className="checkbox-grid">
            {accessibilityOptions.map(option => (
              <label key={option.value} className="checkbox-option">
                <input
                  type="checkbox"
                  checked={formData.accessibility.includes(option.value)}
                  onChange={() => handleMultiSelect('accessibility', option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Clock size={20} />
            Travel Pace
          </h3>
          <div className="pace-options">
            <label className={`pace-option ${formData.travelPace === 'slow' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="travelPace"
                value="slow"
                checked={formData.travelPace === 'slow'}
                onChange={(e) => handleSingleSelect('travelPace', e.target.value)}
              />
              <span>Slow & Relaxed</span>
            </label>
            <label className={`pace-option ${formData.travelPace === 'moderate' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="travelPace"
                value="moderate"
                checked={formData.travelPace === 'moderate'}
                onChange={(e) => handleSingleSelect('travelPace', e.target.value)}
              />
              <span>Moderate</span>
            </label>
            <label className={`pace-option ${formData.travelPace === 'fast' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="travelPace"
                value="fast"
                checked={formData.travelPace === 'fast'}
                onChange={(e) => handleSingleSelect('travelPace', e.target.value)}
              />
              <span>Fast-paced</span>
            </label>
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Users size={20} />
            Typical Group Size
          </h3>
          <div className="group-options">
            <label className={`group-option ${formData.groupSize === 'solo' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="groupSize"
                value="solo"
                checked={formData.groupSize === 'solo'}
                onChange={(e) => handleSingleSelect('groupSize', e.target.value)}
              />
              <span>Solo</span>
            </label>
            <label className={`group-option ${formData.groupSize === 'couple' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="groupSize"
                value="couple"
                checked={formData.groupSize === 'couple'}
                onChange={(e) => handleSingleSelect('groupSize', e.target.value)}
              />
              <span>Couple</span>
            </label>
            <label className={`group-option ${formData.groupSize === 'family' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="groupSize"
                value="family"
                checked={formData.groupSize === 'family'}
                onChange={(e) => handleSingleSelect('groupSize', e.target.value)}
              />
              <span>Family</span>
            </label>
            <label className={`group-option ${formData.groupSize === 'group' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="groupSize"
                value="group"
                checked={formData.groupSize === 'group'}
                onChange={(e) => handleSingleSelect('groupSize', e.target.value)}
              />
              <span>Group</span>
            </label>
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Plane size={20} />
            Preferred Airlines
          </h3>
          <div className="tag-input-container">
            <div className="tag-list">
              {formData.preferredAirlines.map(airline => (
                <span key={airline} className="tag">
                  {airline}
                  <button
                    type="button"
                    onClick={() => handleRemoveItem('preferredAirlines', airline)}
                    className="tag-remove"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
            <div className="tag-input">
              <input
                type="text"
                value={newAirline}
                onChange={(e) => setNewAirline(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddItem('preferredAirlines', newAirline, setNewAirline);
                  }
                }}
                placeholder="Add an airline"
              />
              <button
                type="button"
                onClick={() => handleAddItem('preferredAirlines', newAirline, setNewAirline)}
                className="add-button"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>
        </div>

        <div className="preference-section">
          <h3>
            <Hotel size={20} />
            Preferred Hotel Chains
          </h3>
          <div className="tag-input-container">
            <div className="tag-list">
              {formData.preferredHotelChains.map(hotel => (
                <span key={hotel} className="tag">
                  {hotel}
                  <button
                    type="button"
                    onClick={() => handleRemoveItem('preferredHotelChains', hotel)}
                    className="tag-remove"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
            <div className="tag-input">
              <input
                type="text"
                value={newHotelChain}
                onChange={(e) => setNewHotelChain(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddItem('preferredHotelChains', newHotelChain, setNewHotelChain);
                  }
                }}
                placeholder="Add a hotel chain"
              />
              <button
                type="button"
                onClick={() => handleAddItem('preferredHotelChains', newHotelChain, setNewHotelChain)}
                className="add-button"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default TravelPreferences;