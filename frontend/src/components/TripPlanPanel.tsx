import React, { useState, useCallback } from 'react';
import { useTripPlan } from '../hooks/useTripPlan';
import { FlightOption, HotelOption, ActivityOption } from '../types';
import './TripPlanPanel.css';

interface TripPlanPanelProps {
  sessionId: string;
  isOpen: boolean;
  onClose?: () => void;
}

const TripPlanPanel: React.FC<TripPlanPanelProps> = ({ sessionId, isOpen, onClose }) => {
  const {
    planDays,
    planSummary,
    isLoading,
    error,
    removeItem,
    moveItem,
    updateItemNotes,
    reorderItems,
    exportPlan,
    sharePlan,
    refreshPlan
  } = useTripPlan(sessionId);

  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set([1]));
  const [editingNotes, setEditingNotes] = useState<{ day: number; itemId: string } | null>(null);
  const [noteText, setNoteText] = useState('');
  const [showShareSuccess, setShowShareSuccess] = useState(false);

  // Toggle day expansion
  const toggleDayExpansion = useCallback((day: number) => {
    setExpandedDays(prev => {
      const newSet = new Set(prev);
      if (newSet.has(day)) {
        newSet.delete(day);
      } else {
        newSet.add(day);
      }
      return newSet;
    });
  }, []);

  // Start editing notes
  const startEditingNotes = useCallback((day: number, itemId: string, currentNotes: string) => {
    setEditingNotes({ day, itemId });
    setNoteText(currentNotes || '');
  }, []);

  // Save notes
  const saveNotes = useCallback(async () => {
    if (editingNotes) {
      await updateItemNotes(editingNotes.day, editingNotes.itemId, noteText);
      setEditingNotes(null);
      setNoteText('');
    }
  }, [editingNotes, noteText, updateItemNotes]);

  // Cancel editing notes
  const cancelEditingNotes = useCallback(() => {
    setEditingNotes(null);
    setNoteText('');
  }, []);

  // Handle share button click
  const handleShare = useCallback(async () => {
    try {
      await sharePlan();
      setShowShareSuccess(true);
      setTimeout(() => setShowShareSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to share plan:', err);
    }
  }, [sharePlan]);

  // Format price
  const formatPrice = (price: { amount: number; currency: string }) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: price.currency
    }).format(price.amount);
  };

  // Get item icon based on type
  const getItemIcon = (type: string) => {
    switch (type) {
      case 'flight':
        return '✈️';
      case 'hotel':
        return '🏨';
      case 'activity':
        return '🎫';
      case 'note':
        return '📝';
      default:
        return '📍';
    }
  };

  // Render item details based on type
  const renderItemDetails = (item: any) => {
    switch (item.type) {
      case 'flight':
        const flight = item.data as FlightOption;
        return (
          <div className="item-details flight-details">
            <div className="flight-route">
              <span className="airport">{flight.origin.code}</span>
              <span className="arrow">→</span>
              <span className="airport">{flight.destination.code}</span>
            </div>
            <div className="flight-info">
              <span className="airline">{flight.airline} {flight.flightNumber}</span>
              <span className="duration">{flight.duration}</span>
            </div>
          </div>
        );
      
      case 'hotel':
        const hotel = item.data as HotelOption;
        return (
          <div className="item-details hotel-details">
            <div className="hotel-name">{hotel.name}</div>
            <div className="hotel-info">
              <span className="rating">{'★'.repeat(Math.floor(hotel.rating))}</span>
              <span className="location">{hotel.location.city}</span>
            </div>
          </div>
        );
      
      case 'activity':
        const activity = item.data as ActivityOption;
        return (
          <div className="item-details activity-details">
            <div className="activity-name">{activity.name}</div>
            <div className="activity-info">
              <span className="duration">{activity.duration}</span>
              {activity.rating && <span className="rating">{activity.rating}★</span>}
            </div>
          </div>
        );
      
      case 'note':
        const note = item.data as { content: string };
        return (
          <div className="item-details note-details">
            <div className="note-content">{note.content}</div>
          </div>
        );
      
      default:
        return null;
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="trip-plan-panel">
      <div className="panel-header">
        <h2>Trip Plan</h2>
        <div className="panel-actions">
          <button onClick={refreshPlan} className="refresh-button" title="Refresh">
            🔄
          </button>
          <button onClick={exportPlan} className="export-button" title="Export">
            💾
          </button>
          <button onClick={handleShare} className="share-button" title="Share">
            🔗
          </button>
          {onClose && (
            <button onClick={onClose} className="close-button" title="Close">
              ✕
            </button>
          )}
        </div>
      </div>

      {showShareSuccess && (
        <div className="share-success-message">
          Link copied to clipboard! 📋
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading trip plan...</p>
        </div>
      ) : planSummary ? (
        <>
          {/* Trip Summary */}
          <div className="trip-summary">
            <h3>{planSummary.destination}</h3>
            <div className="summary-details">
              <div className="summary-item">
                <span className="label">Dates:</span>
                <span className="value">
                  {new Date(planSummary.departureDate).toLocaleDateString()} - {new Date(planSummary.returnDate).toLocaleDateString()}
                </span>
              </div>
              <div className="summary-item">
                <span className="label">Travelers:</span>
                <span className="value">{planSummary.travelers}</span>
              </div>
              <div className="summary-item">
                <span className="label">Status:</span>
                <span className={`status ${planSummary.status}`}>{planSummary.status}</span>
              </div>
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="cost-breakdown">
            <h4>Total Cost: {formatPrice(planSummary.totalCost)}</h4>
            <div className="cost-details">
              <div className="cost-item">
                <span>Flights:</span>
                <span>{formatPrice({ amount: planSummary.totalCost.breakdown.flights, currency: planSummary.totalCost.currency })}</span>
              </div>
              <div className="cost-item">
                <span>Hotels:</span>
                <span>{formatPrice({ amount: planSummary.totalCost.breakdown.hotels, currency: planSummary.totalCost.currency })}</span>
              </div>
              <div className="cost-item">
                <span>Activities:</span>
                <span>{formatPrice({ amount: planSummary.totalCost.breakdown.activities, currency: planSummary.totalCost.currency })}</span>
              </div>
            </div>
          </div>

          {/* Day-by-day Itinerary */}
          <div className="itinerary">
            <h4>Itinerary</h4>
            {planDays.map(day => (
              <div key={day.day} className={`day-container ${expandedDays.has(day.day) ? 'expanded' : ''}`}>
                <div className="day-header" onClick={() => toggleDayExpansion(day.day)}>
                  <h5>Day {day.day} - {new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</h5>
                  <span className="item-count">{day.items.length} items</span>
                  <span className="expand-icon">{expandedDays.has(day.day) ? '▼' : '▶'}</span>
                </div>
                
                {expandedDays.has(day.day) && (
                  <div className="day-items">
                    {day.items.length === 0 ? (
                      <div className="empty-day">No items planned for this day</div>
                    ) : (
                      day.items.map(item => (
                        <div key={item.id} className={`plan-item ${item.type} ${item.isBooked ? 'booked' : ''}`}>
                          <div className="item-header">
                            <span className="item-icon">{getItemIcon(item.type)}</span>
                            {item.time && <span className="item-time">{item.time}</span>}
                            {item.isBooked && <span className="booked-badge">Booked</span>}
                          </div>
                          
                          {renderItemDetails(item)}
                          
                          {item.type !== 'note' && (
                            <div className="item-price">
                              {formatPrice((item.data as any).price)}
                            </div>
                          )}
                          
                          {/* Notes section */}
                          <div className="item-notes">
                            {editingNotes?.itemId === item.id ? (
                              <div className="notes-editor">
                                <textarea
                                  value={noteText}
                                  onChange={(e) => setNoteText(e.target.value)}
                                  placeholder="Add notes..."
                                  rows={3}
                                />
                                <div className="notes-actions">
                                  <button onClick={saveNotes} className="save-notes">Save</button>
                                  <button onClick={cancelEditingNotes} className="cancel-notes">Cancel</button>
                                </div>
                              </div>
                            ) : (
                              <>
                                {item.notes && <p className="notes-text">{item.notes}</p>}
                                <button
                                  onClick={() => startEditingNotes(day.day, item.id, item.notes || '')}
                                  className="edit-notes-button"
                                >
                                  {item.notes ? 'Edit notes' : 'Add notes'}
                                </button>
                              </>
                            )}
                          </div>
                          
                          {/* Item actions */}
                          <div className="item-actions">
                            <button
                              onClick={() => removeItem(day.day, item.id)}
                              className="remove-item"
                              title="Remove from trip"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <p>No trip plan yet. Start adding items to create your itinerary!</p>
        </div>
      )}
    </div>
  );
};

export default TripPlanPanel;