import React, { useState, useCallback, useMemo } from 'react';
import { useTripPlan } from '../hooks/useTripPlan';
import { FlightOption, HotelOption, ActivityOption } from '../types';
import { formatDate } from '../utils/dateHelpers';
import TripDayDetailsModal from './TripDayDetailsModal';
import '../styles/components/EnhancedTripPlanPanel.css';

interface EnhancedTripPlanPanelProps {
  sessionId: string;
  isOpen: boolean;
  onClose?: () => void;
  selectedDates?: {
    startDate: string;
    endDate: string;
  };
}

type ItemType = 'all' | 'flights' | 'hotels' | 'activities';

const EnhancedTripPlanPanel: React.FC<EnhancedTripPlanPanelProps> = ({ 
  sessionId, 
  isOpen, 
  onClose,
  selectedDates 
}) => {
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

  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [selectedItemType, setSelectedItemType] = useState<ItemType>('all');
  const [editingNotes, setEditingNotes] = useState<{ day: number; itemId: string } | null>(null);
  const [noteText, setNoteText] = useState('');
  const [showShareSuccess, setShowShareSuccess] = useState(false);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedDayData, setSelectedDayData] = useState<any>(null);

  // Filter items by type for the selected day
  const filteredItems = useMemo(() => {
    const currentDay = planDays.find(day => day.day === selectedDay);
    if (!currentDay) return [];

    if (selectedItemType === 'all') {
      return currentDay.items;
    }

    const typeMap = {
      flights: 'flight',
      hotels: 'hotel', 
      activities: 'activity'
    };

    return currentDay.items.filter(item => item.type === typeMap[selectedItemType]);
  }, [planDays, selectedDay, selectedItemType]);

  // Get item counts by type for current day
  const getItemCounts = useMemo(() => {
    const currentDay = planDays.find(day => day.day === selectedDay);
    if (!currentDay) return { all: 0, flights: 0, hotels: 0, activities: 0 };

    return {
      all: currentDay.items.length,
      flights: currentDay.items.filter(item => item.type === 'flight').length,
      hotels: currentDay.items.filter(item => item.type === 'hotel').length,
      activities: currentDay.items.filter(item => item.type === 'activity').length
    };
  }, [planDays, selectedDay]);

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

  // Handle clicking on a day to show details
  const handleDayClick = useCallback((dayData: any) => {
    setSelectedDayData(dayData);
    setDetailsModalOpen(true);
  }, []);

  // Close details modal
  const handleCloseDetails = useCallback(() => {
    setDetailsModalOpen(false);
    setSelectedDayData(null);
  }, []);

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

  // Get activity indicators for a day
  const getDayIndicators = (dayItems: any[]) => {
    const indicators = [];
    if (dayItems.some(item => item.type === 'flight')) indicators.push('✈️');
    if (dayItems.some(item => item.type === 'hotel')) indicators.push('🏨');
    if (dayItems.some(item => item.type === 'activity')) indicators.push('🎫');
    return indicators;
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
    <div className="enhanced-trip-plan-panel">
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
                  {selectedDates ? (
                    `${formatDate(selectedDates.startDate, 'short')} - ${formatDate(selectedDates.endDate, 'short')}`
                  ) : (
                    `${new Date(planSummary.departureDate).toLocaleDateString()} - ${new Date(planSummary.returnDate).toLocaleDateString()}`
                  )}
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

          {/* Date Tabs Navigation */}
          {planDays.length > 0 && (
            <div className="date-tabs-container">
              <div className="date-tabs">
                {planDays.map(day => (
                  <button
                    key={day.day}
                    className={`date-tab ${selectedDay === day.day ? 'active' : ''}`}
                    onClick={() => setSelectedDay(day.day)}
                  >
                    <div className="date-tab-content">
                      <div className="day-label">Day {day.day}</div>
                      <div 
                        className="date-label clickable-date" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDayClick(day);
                        }}
                        title="Click to view flight and hotel details"
                      >
                        {formatDate(day.date, 'short')}
                        <span className="details-icon">🔍</span>
                      </div>
                      <div className="activity-indicators">
                        {getDayIndicators(day.items).map((indicator, index) => (
                          <span key={index} className="indicator">{indicator}</span>
                        ))}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Type Filter Tabs */}
              <div className="type-filter-tabs">
                <button
                  className={`type-tab ${selectedItemType === 'all' ? 'active' : ''}`}
                  onClick={() => setSelectedItemType('all')}
                >
                  All ({getItemCounts.all})
                </button>
                <button
                  className={`type-tab ${selectedItemType === 'flights' ? 'active' : ''}`}
                  onClick={() => setSelectedItemType('flights')}
                >
                  ✈️ Flights ({getItemCounts.flights})
                </button>
                <button
                  className={`type-tab ${selectedItemType === 'hotels' ? 'active' : ''}`}
                  onClick={() => setSelectedItemType('hotels')}
                >
                  🏨 Hotels ({getItemCounts.hotels})
                </button>
                <button
                  className={`type-tab ${selectedItemType === 'activities' ? 'active' : ''}`}
                  onClick={() => setSelectedItemType('activities')}
                >
                  🎫 Activities ({getItemCounts.activities})
                </button>
              </div>
            </div>
          )}

          {/* Filtered Items Display */}
          <div className="filtered-items">
            {filteredItems.length > 0 ? (
              <div className="items-list">
                {filteredItems.map(item => (
                  <div key={item.id} className="trip-item">
                    <div className="item-header">
                      <span className="item-icon">{getItemIcon(item.type)}</span>
                      <div className="item-title">
                        {renderItemDetails(item)}
                      </div>
                      <div className="item-actions">
                        <button
                          onClick={() => startEditingNotes(selectedDay, item.id, item.notes || '')}
                          className="edit-notes-button"
                          title="Edit notes"
                        >
                          📝
                        </button>
                        <button
                          onClick={() => removeItem(selectedDay, item.id)}
                          className="remove-item-button"
                          title="Remove item"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>

                    {/* Item Notes */}
                    {editingNotes?.itemId === item.id ? (
                      <div className="note-editor">
                        <textarea
                          value={noteText}
                          onChange={(e) => setNoteText(e.target.value)}
                          placeholder="Add notes for this item..."
                          className="note-textarea"
                        />
                        <div className="note-actions">
                          <button onClick={saveNotes} className="save-note-button">
                            Save
                          </button>
                          <button onClick={cancelEditingNotes} className="cancel-note-button">
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : item.notes ? (
                      <div className="item-notes">
                        <p>{item.notes}</p>
                      </div>
                    ) : null}

                    {/* Item Price */}
                    {item.type !== 'note' && (
                      <div className="item-price">
                        {formatPrice((item.data as any).price)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-items">
                <p>No {selectedItemType === 'all' ? 'items' : selectedItemType} for Day {selectedDay}</p>
                <p className="empty-hint">Add items to your trip plan to see them here.</p>
              </div>
            )}
          </div>

          {/* Cost Breakdown */}
          {planSummary.totalCost && (
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
          )}
        </>
      ) : (
        <div className="empty-plan">
          <p>No trip plan available</p>
          <p className="empty-hint">Start planning your trip to see details here.</p>
        </div>
      )}

      {/* Trip Day Details Modal */}
      <TripDayDetailsModal
        isOpen={detailsModalOpen}
        onClose={handleCloseDetails}
        dayData={selectedDayData}
      />
    </div>
  );
};

export default EnhancedTripPlanPanel;