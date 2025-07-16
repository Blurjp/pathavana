import React, { useState, useEffect } from 'react';
import { Save, Camera, Calendar, Mail, Phone, MapPin } from 'lucide-react';
import '../../styles/components/profile/PersonalInfo.css';

interface PersonalInfoProps {
  profile: any;
  onUpdate: (data: any) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const PersonalInfo: React.FC<PersonalInfoProps> = ({
  profile,
  onUpdate,
  loading,
  error,
}) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    location: '',
    bio: '',
    avatar: '',
  });
  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  useEffect(() => {
    if (profile) {
      // Split full_name into firstName and lastName
      const nameParts = profile.full_name?.split(' ') || [];
      const firstName = nameParts[0] || profile.firstName || '';
      const lastName = nameParts.slice(1).join(' ') || profile.lastName || '';
      
      setFormData({
        firstName,
        lastName,
        email: profile.email || '',
        phone: profile.phone || '',
        dateOfBirth: profile.dateOfBirth || '',
        location: profile.location || '',
        bio: profile.bio || '',
        avatar: profile.avatar || '',
      });
    }
  }, [profile]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setIsEditing(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');
    
    try {
      // Combine firstName and lastName into full_name
      const updateData = {
        ...formData,
        full_name: `${formData.firstName} ${formData.lastName}`.trim()
      };
      
      await onUpdate(updateData);
      setSaveStatus('saved');
      setIsEditing(false);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err) {
      setSaveStatus('idle');
      console.error('Failed to update profile:', err);
    }
  };

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In a real app, you would upload this to a server
      // For now, we'll create a local URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData(prev => ({ ...prev, avatar: reader.result as string }));
        setIsEditing(true);
      };
      reader.readAsDataURL(file);
    }
  };

  const getInitials = () => {
    const first = formData.firstName?.charAt(0) || '';
    const last = formData.lastName?.charAt(0) || '';
    return (first + last).toUpperCase() || 'U';
  };

  return (
    <div className="personal-info">
      <form onSubmit={handleSubmit}>
        <div className="info-header">
          <h2>Personal Information</h2>
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

        <div className="avatar-section">
          <div className="avatar-container">
            {formData.avatar ? (
              <img src={formData.avatar} alt="Profile" className="avatar-image" />
            ) : (
              <div className="avatar-placeholder">
                {getInitials()}
              </div>
            )}
            <label htmlFor="avatar-upload" className="avatar-upload">
              <Camera size={20} />
              <input
                id="avatar-upload"
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="firstName">First Name</label>
            <input
              id="firstName"
              name="firstName"
              type="text"
              value={formData.firstName}
              onChange={handleInputChange}
              placeholder="Enter your first name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastName">Last Name</label>
            <input
              id="lastName"
              name="lastName"
              type="text"
              value={formData.lastName}
              onChange={handleInputChange}
              placeholder="Enter your last name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">
              <Mail size={16} />
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="your@email.com"
              disabled={profile?.emailVerified}
            />
            {profile?.emailVerified && (
              <span className="verified-badge">Verified</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="phone">
              <Phone size={16} />
              Phone Number
            </label>
            <input
              id="phone"
              name="phone"
              type="tel"
              value={formData.phone}
              onChange={handleInputChange}
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div className="form-group">
            <label htmlFor="dateOfBirth">
              <Calendar size={16} />
              Date of Birth
            </label>
            <input
              id="dateOfBirth"
              name="dateOfBirth"
              type="date"
              value={formData.dateOfBirth}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="location">
              <MapPin size={16} />
              Location
            </label>
            <input
              id="location"
              name="location"
              type="text"
              value={formData.location}
              onChange={handleInputChange}
              placeholder="City, Country"
            />
          </div>
        </div>

        <div className="form-group full-width">
          <label htmlFor="bio">Bio</label>
          <textarea
            id="bio"
            name="bio"
            value={formData.bio}
            onChange={handleInputChange}
            placeholder="Tell us a bit about yourself..."
            rows={4}
          />
        </div>
      </form>
    </div>
  );
};

export default PersonalInfo;