import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Globe, Bell, Shield } from 'lucide-react';
import PersonalInfo from '../components/profile/PersonalInfo';
import TravelPreferences from '../components/profile/TravelPreferences';
import useUserProfile from '../hooks/useUserProfile';
import '../styles/pages/ProfileSettings.css';

type TabType = 'personal' | 'preferences' | 'notifications' | 'privacy';

const ProfileSettings: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('personal');
  const { profile, loading, error, updateProfile } = useUserProfile();

  const tabs = [
    { id: 'personal', label: 'Personal Info', icon: User },
    { id: 'preferences', label: 'Travel Preferences', icon: Globe },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy & Security', icon: Shield },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'personal':
        return (
          <PersonalInfo
            profile={profile}
            onUpdate={updateProfile}
            loading={loading}
            error={error}
          />
        );
      case 'preferences':
        return (
          <TravelPreferences
            preferences={profile?.preferences}
            onUpdate={(preferences) => updateProfile({ preferences })}
            loading={loading}
            error={error}
          />
        );
      case 'notifications':
        return (
          <div className="tab-content">
            <h3>Notification Settings</h3>
            <p className="coming-soon">Coming soon...</p>
          </div>
        );
      case 'privacy':
        return (
          <div className="tab-content">
            <h3>Privacy & Security</h3>
            <p className="coming-soon">Coming soon...</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="profile-settings">
      <div className="profile-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          <ArrowLeft size={20} />
          <span>Back</span>
        </button>
        <h1>Profile Settings</h1>
      </div>

      <div className="profile-content">
        <div className="profile-tabs">
          <nav className="tabs-nav">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id as TabType)}
                >
                  <Icon size={20} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="profile-main">
          {loading && !profile ? (
            <div className="loading-state">
              <div className="loader"></div>
              <p>Loading profile...</p>
            </div>
          ) : error && !profile ? (
            <div className="error-state">
              <p>Error loading profile: {error}</p>
              <button onClick={() => window.location.reload()}>
                Try Again
              </button>
            </div>
          ) : (
            renderTabContent()
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;