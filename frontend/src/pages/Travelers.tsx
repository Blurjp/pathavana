import React, { useState } from 'react';
import TravelerList from '../components/travelers/TravelerList';
import TravelerForm from '../components/travelers/TravelerForm';
import { useTravelers } from '../hooks/useTravelers';
import { TravelerProfile } from '../types';
import { LegacyTravelerProfile, legacyToNewTraveler, newToLegacyTraveler } from '../types/TravelerFormTypes';
import '../styles/pages/Travelers.css';

const Travelers: React.FC = () => {
  const {
    travelers,
    isLoading,
    error,
    createTraveler,
    updateTraveler,
    deleteTraveler,
    refreshTravelers
  } = useTravelers();

  const [showForm, setShowForm] = useState(false);
  const [editingTraveler, setEditingTraveler] = useState<TravelerProfile | null>(null);
  const [editingLegacyTraveler, setEditingLegacyTraveler] = useState<LegacyTravelerProfile | null>(null);

  const handleAddClick = () => {
    setEditingTraveler(null);
    setEditingLegacyTraveler(null);
    setShowForm(true);
  };

  const handleEditClick = (traveler: TravelerProfile) => {
    setEditingTraveler(traveler);
    setEditingLegacyTraveler(newToLegacyTraveler(traveler));
    setShowForm(true);
  };

  const handleFormSubmit = async (data: Partial<LegacyTravelerProfile>) => {
    try {
      const newFormatData = legacyToNewTraveler(data);
      if (editingTraveler) {
        await updateTraveler(editingTraveler.id, newFormatData);
      } else {
        await createTraveler(newFormatData);
      }
      setShowForm(false);
      setEditingTraveler(null);
      setEditingLegacyTraveler(null);
    } catch (error) {
      // Error is handled by the hook
      console.error('Failed to save traveler:', error);
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingTraveler(null);
    setEditingLegacyTraveler(null);
  };

  const handleDeleteClick = async (travelerId: string) => {
    if (window.confirm('Are you sure you want to delete this traveler profile?')) {
      await deleteTraveler(travelerId);
    }
  };

  return (
    <div className="travelers-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Traveler Profiles</h1>
          <p className="page-description">
            Manage traveler profiles for your trips. Add family members, friends, or colleagues
            to easily include them in your travel plans.
          </p>
        </div>
        <button
          onClick={handleAddClick}
          className="btn-primary add-traveler-btn"
          disabled={isLoading}
        >
          <span className="icon">+</span>
          Add Traveler
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={refreshTravelers} className="retry-btn">
            Try Again
          </button>
        </div>
      )}

      <TravelerList
        travelers={travelers}
        isLoading={isLoading}
        onEdit={handleEditClick}
        onDelete={handleDeleteClick}
        onAddClick={handleAddClick}
      />

      {showForm && (
        <div className="modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) handleFormCancel();
        }}>
          <div className="modal-content">
            <div className="modal-header">
              <h2>{editingTraveler ? 'Edit Traveler' : 'Add New Traveler'}</h2>
              <button
                onClick={handleFormCancel}
                className="close-button"
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <TravelerForm
              traveler={editingLegacyTraveler}
              onSubmit={handleFormSubmit}
              onCancel={handleFormCancel}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Travelers;