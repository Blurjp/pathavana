import React from 'react';
import TravelerCard from './TravelerCard';
import { TravelerProfile } from '../../types';
import '../../styles/components/TravelerList.css';

interface TravelerListProps {
  travelers: TravelerProfile[];
  isLoading: boolean;
  onEdit: (traveler: TravelerProfile) => void;
  onDelete: (travelerId: string) => void;
  onAddClick: () => void;
}

const TravelerList: React.FC<TravelerListProps> = ({
  travelers,
  isLoading,
  onEdit,
  onDelete,
  onAddClick
}) => {
  if (isLoading) {
    return (
      <div className="traveler-list-loading">
        <div className="loading-spinner" />
        <p>Loading travelers...</p>
      </div>
    );
  }

  if (travelers.length === 0) {
    return (
      <div className="traveler-list-empty">
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <h3>No traveler profiles yet</h3>
          <p>
            Add traveler profiles to save their preferences and information for future trips.
            This makes it easy to book travel for family, friends, or colleagues.
          </p>
          <button onClick={onAddClick} className="btn-primary">
            Add Your First Traveler
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="traveler-list">
      <div className="traveler-grid">
        {travelers.map((traveler) => (
          <TravelerCard
            key={traveler.id}
            traveler={traveler}
            onEdit={() => onEdit(traveler)}
            onDelete={() => onDelete(traveler.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default TravelerList;