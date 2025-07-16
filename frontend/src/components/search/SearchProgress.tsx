import React from 'react';
import '../../styles/components/SearchProgress.css';

interface SearchProgressProps {
  type: 'flight' | 'hotel' | 'activity';
  status: 'searching' | 'found' | 'none' | 'error';
  count?: number;
  error?: string;
}

const SearchProgress: React.FC<SearchProgressProps> = ({ type, status, count, error }) => {
  const getIcon = () => {
    switch (type) {
      case 'flight':
        return '✈️';
      case 'hotel':
        return '🏨';
      case 'activity':
        return '🎯';
      default:
        return '🔍';
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'searching':
        return `Searching for ${type}s...`;
      case 'found':
        return `Found ${count || 0} ${type}${count === 1 ? '' : 's'}`;
      case 'none':
        return `No ${type}s found matching your criteria`;
      case 'error':
        return error || `Error searching for ${type}s`;
      default:
        return '';
    }
  };

  const getStatusClass = () => {
    switch (status) {
      case 'searching':
        return 'searching';
      case 'found':
        return 'found';
      case 'none':
        return 'none';
      case 'error':
        return 'error';
      default:
        return '';
    }
  };

  return (
    <div className={`search-progress ${getStatusClass()}`}>
      <span className="search-icon">{getIcon()}</span>
      <span className="search-message">{getStatusMessage()}</span>
      {status === 'searching' && (
        <span className="search-spinner">
          <span className="spinner"></span>
        </span>
      )}
      {status === 'found' && count && count > 0 && (
        <span className="search-action">Click to view in sidebar →</span>
      )}
    </div>
  );
};

export default SearchProgress;