import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Trip, TravelSession } from '../types';
import { travelApi } from '../services/travelApi';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { formatDate, formatDateTime } from '../utils/dateHelpers';
import { handleApiError } from '../utils/errorHandler';
import { AuthGuard } from '../components/auth/AuthGuard';

const Trips: React.FC = () => {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [sessions, setSessions] = useState<TravelSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'saved' | 'planning'>('saved');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (activeTab === 'saved') {
        await loadTrips();
      } else {
        await loadSessions();
      }
    } catch (err: any) {
      setError(handleApiError(err, 'trips'));
    } finally {
      setIsLoading(false);
    }
  };

  const loadTrips = async () => {
    const response = await travelApi.getTrips();
    if (response.success && response.data) {
      setTrips(response.data);
    } else {
      throw new Error(response.error || 'Failed to load trips');
    }
  };

  const loadSessions = async () => {
    // Note: This would need to be implemented in the API
    // For now, we'll show a placeholder
    setSessions([]);
  };

  const handleDeleteTrip = async (tripId: string) => {
    if (!window.confirm('Are you sure you want to delete this trip?')) {
      return;
    }

    try {
      const response = await travelApi.deleteTrip(tripId);
      if (response.success) {
        setTrips(prev => prev.filter(trip => trip.id !== tripId));
      } else {
        throw new Error(response.error || 'Failed to delete trip');
      }
    } catch (err: any) {
      setError(handleApiError(err, 'delete_trip'));
    }
  };

  const getStatusIcon = (status: Trip['status']) => {
    switch (status) {
      case 'planning':
        return '📋';
      case 'booked':
        return '✈️';
      case 'completed':
        return '✅';
      case 'cancelled':
        return '❌';
      default:
        return '📋';
    }
  };

  const getStatusColor = (status: Trip['status']) => {
    switch (status) {
      case 'planning':
        return 'blue';
      case 'booked':
        return 'green';
      case 'completed':
        return 'gray';
      case 'cancelled':
        return 'red';
      default:
        return 'blue';
    }
  };

  const renderTripCard = (trip: Trip) => (
    <div key={trip.id} className="trip-card">
      <div className="trip-header">
        <div className="trip-title">
          <h3>{trip.name}</h3>
          <span className={`status ${getStatusColor(trip.status)}`}>
            {getStatusIcon(trip.status)} {trip.status}
          </span>
        </div>
        <div className="trip-actions">
          <Link to={`/trips/${trip.id}`} className="btn-secondary">
            View Details
          </Link>
          <button
            onClick={() => handleDeleteTrip(trip.id)}
            className="btn-danger"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="trip-content">
        <div className="trip-destination">
          <span className="label">📍 Destination:</span>
          <span className="value">{trip.destination}</span>
        </div>

        <div className="trip-dates">
          <span className="label">📅 Dates:</span>
          <span className="value">
            {formatDate(trip.startDate)} - {formatDate(trip.endDate)}
          </span>
        </div>

        {trip.travelers.length > 0 && (
          <div className="trip-travelers">
            <span className="label">👥 Travelers:</span>
            <span className="value">
              {trip.travelers.map(t => t.name).join(', ')}
            </span>
          </div>
        )}

        {trip.budget && (
          <div className="trip-budget">
            <span className="label">💰 Budget:</span>
            <span className="value">${trip.budget.toLocaleString()}</span>
          </div>
        )}

        {trip.description && (
          <div className="trip-description">
            <p>{trip.description}</p>
          </div>
        )}

        <div className="trip-meta">
          <span>Created {formatDateTime(trip.createdAt)}</span>
          {trip.updatedAt !== trip.createdAt && (
            <span>Updated {formatDateTime(trip.updatedAt)}</span>
          )}
        </div>
      </div>

      {trip.itinerary.length > 0 && (
        <div className="trip-preview">
          <h4>Itinerary Preview</h4>
          <div className="itinerary-items">
            {trip.itinerary.slice(0, 3).map((item) => (
              <div key={item.id} className="itinerary-item">
                <span className="type">{item.type}</span>
                <span className="title">{item.title}</span>
                <span className="time">{formatDate(item.startTime)}</span>
              </div>
            ))}
            {trip.itinerary.length > 3 && (
              <div className="more-items">
                +{trip.itinerary.length - 3} more items
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderSessionCard = (session: TravelSession) => (
    <div key={session.id} className="session-card">
      <div className="session-header">
        <div className="session-title">
          <h3>Planning Session</h3>
          <span className={`status ${session.status}`}>
            {session.status}
          </span>
        </div>
        <div className="session-actions">
          <Link to={`/chat/${session.id}`} className="btn-primary">
            Continue
          </Link>
        </div>
      </div>

      <div className="session-content">
        <div className="session-messages">
          <span className="label">💬 Messages:</span>
          <span className="value">{session.messages.length}</span>
        </div>

        {session.context.currentRequest?.destination && (
          <div className="session-destination">
            <span className="label">📍 Planning for:</span>
            <span className="value">{session.context.currentRequest.destination}</span>
          </div>
        )}

        <div className="session-meta">
          <span>Started {formatDateTime(session.createdAt)}</span>
          <span>Last active {formatDateTime(session.updatedAt)}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="trips-page">
      <div className="page-header">
        <h1>My Trips</h1>
        <div className="page-actions">
          <Link to="/chat" className="btn-primary">
            Plan New Trip
          </Link>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="tab-navigation">
        <button
          onClick={() => setActiveTab('saved')}
          className={`tab ${activeTab === 'saved' ? 'active' : ''}`}
        >
          Saved Trips ({trips.length})
        </button>
        <button
          onClick={() => setActiveTab('planning')}
          className={`tab ${activeTab === 'planning' ? 'active' : ''}`}
        >
          Planning Sessions ({sessions.length})
        </button>
      </div>

      {/* Content area */}
      <div className="trips-content">
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner large" />
            <p>Loading your trips...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <div className="error-icon">⚠️</div>
            <h3>Something went wrong</h3>
            <p>{error}</p>
            <button onClick={loadData} className="btn-primary">
              Try Again
            </button>
          </div>
        ) : (
          <>
            {activeTab === 'saved' && (
              <div className="trips-grid">
                {trips.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">✈️</div>
                    <h3>No saved trips yet</h3>
                    <p>Start planning your first trip to see it here</p>
                    <Link to="/chat" className="btn-primary">
                      Plan Your First Trip
                    </Link>
                  </div>
                ) : (
                  trips.map(renderTripCard)
                )}
              </div>
            )}

            {activeTab === 'planning' && (
              <div className="sessions-grid">
                {sessions.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">💬</div>
                    <h3>No active planning sessions</h3>
                    <p>Start a conversation to begin planning a trip</p>
                    <Link to="/chat" className="btn-primary">
                      Start Planning
                    </Link>
                  </div>
                ) : (
                  sessions.map(renderSessionCard)
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

const TripsWithAuth: React.FC = () => (
  <AuthGuard>
    <Trips />
  </AuthGuard>
);

export default TripsWithAuth;