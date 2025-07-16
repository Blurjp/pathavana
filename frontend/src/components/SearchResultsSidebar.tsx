import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useSidebar } from '../contexts/SidebarContext';
import { SearchResults, FlightOption, HotelOption, ActivityOption, ItineraryItem } from '../types';
import FlightCard from './FlightCard';
import HotelCard from './HotelCard';
import ActivityCard from './ActivityCard';
import TripPlanPanel from './TripPlanPanel';
import '../styles/components/SearchResultsSidebar.css';

interface SearchResultsSidebarProps {
  searchResults?: SearchResults;
  isLoading?: boolean;
  onAddToTrip?: (item: ItineraryItem) => void;
  sessionId?: string;
}

type SortOption = 'price-asc' | 'price-desc' | 'rating' | 'duration' | 'departure';
type FilterOptions = {
  priceRange: { min: number; max: number };
  rating: number;
  amenities: string[];
  airlines: string[];
  stops: number | null;
  departureTime: 'morning' | 'afternoon' | 'evening' | 'night' | null;
};

const SearchResultsSidebar: React.FC<SearchResultsSidebarProps> = ({
  searchResults,
  isLoading = false,
  onAddToTrip,
  sessionId
}) => {
  const { 
    sidebarOpen, 
    activeTab, 
    setActiveTab, 
    selectedItems, 
    toggleItemSelection,
    clearSelections,
    getSelectedCount,
    toggleSidebar
  } = useSidebar();

  const [sortBy, setSortBy] = useState<SortOption>('price-asc');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    priceRange: { min: 0, max: 10000 },
    rating: 0,
    amenities: [],
    airlines: [],
    stops: null,
    departureTime: null
  });

  const hasResults = searchResults && (
    (searchResults.flights && searchResults.flights.length > 0) ||
    (searchResults.hotels && searchResults.hotels.length > 0) ||
    (searchResults.activities && searchResults.activities.length > 0)
  );

  const selectedCount = getSelectedCount();

  // Automatically open sidebar when new results arrive
  useEffect(() => {
    if (searchResults && hasResults && !sidebarOpen) {
      toggleSidebar();
      
      // Set active tab based on which results are available
      if (searchResults.flights && searchResults.flights.length > 0) {
        setActiveTab('flights');
      } else if (searchResults.hotels && searchResults.hotels.length > 0) {
        setActiveTab('hotels');
      } else if (searchResults.activities && searchResults.activities.length > 0) {
        setActiveTab('activities');
      }
    }
  }, [searchResults]); // eslint-disable-line react-hooks/exhaustive-deps

  // Extract unique filter options from results
  const filterOptions = useMemo(() => {
    const options = {
      airlines: new Set<string>(),
      amenities: new Set<string>(),
      maxPrice: 0,
      minPrice: Infinity
    };

    if (searchResults?.flights) {
      searchResults.flights.forEach(flight => {
        options.airlines.add(flight.airline);
        options.maxPrice = Math.max(options.maxPrice, flight.price.amount);
        options.minPrice = Math.min(options.minPrice, flight.price.amount);
      });
    }

    if (searchResults?.hotels) {
      searchResults.hotels.forEach(hotel => {
        hotel.amenities.forEach(amenity => options.amenities.add(amenity));
        options.maxPrice = Math.max(options.maxPrice, hotel.price.amount);
        options.minPrice = Math.min(options.minPrice, hotel.price.amount);
      });
    }

    if (searchResults?.activities) {
      searchResults.activities.forEach(activity => {
        options.maxPrice = Math.max(options.maxPrice, activity.price.amount);
        options.minPrice = Math.min(options.minPrice, activity.price.amount);
      });
    }

    return {
      airlines: Array.from(options.airlines).sort(),
      amenities: Array.from(options.amenities).sort(),
      maxPrice: options.maxPrice,
      minPrice: options.minPrice === Infinity ? 0 : options.minPrice
    };
  }, [searchResults]);

  // Filter and sort functions
  const filterFlights = useCallback((flights: FlightOption[]): FlightOption[] => {
    return flights.filter(flight => {
      if (flight.price.amount < filters.priceRange.min || flight.price.amount > filters.priceRange.max) {
        return false;
      }
      if (filters.airlines.length > 0 && !filters.airlines.includes(flight.airline)) {
        return false;
      }
      if (filters.stops !== null && flight.stops !== filters.stops) {
        return false;
      }
      if (filters.departureTime) {
        const hour = new Date(flight.departureTime).getHours();
        switch (filters.departureTime) {
          case 'morning': return hour >= 6 && hour < 12;
          case 'afternoon': return hour >= 12 && hour < 18;
          case 'evening': return hour >= 18 && hour < 22;
          case 'night': return hour >= 22 || hour < 6;
        }
      }
      return true;
    });
  }, [filters]);

  const filterHotels = useCallback((hotels: HotelOption[]): HotelOption[] => {
    return hotels.filter(hotel => {
      if (hotel.price.amount < filters.priceRange.min || hotel.price.amount > filters.priceRange.max) {
        return false;
      }
      if (filters.rating > 0 && hotel.rating < filters.rating) {
        return false;
      }
      if (filters.amenities.length > 0) {
        const hasAllAmenities = filters.amenities.every(amenity => 
          hotel.amenities.includes(amenity)
        );
        if (!hasAllAmenities) return false;
      }
      return true;
    });
  }, [filters]);

  const filterActivities = useCallback((activities: ActivityOption[]): ActivityOption[] => {
    return activities.filter(activity => {
      if (activity.price.amount < filters.priceRange.min || activity.price.amount > filters.priceRange.max) {
        return false;
      }
      if (filters.rating > 0 && activity.rating && activity.rating < filters.rating) {
        return false;
      }
      return true;
    });
  }, [filters]);

  const sortItems = useCallback(<T extends { price: { amount: number }, rating?: number }>(
    items: T[], 
    sortBy: SortOption
  ): T[] => {
    const sorted = [...items];
    switch (sortBy) {
      case 'price-asc':
        return sorted.sort((a, b) => a.price.amount - b.price.amount);
      case 'price-desc':
        return sorted.sort((a, b) => b.price.amount - a.price.amount);
      case 'rating':
        return sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      case 'duration':
        // Only applicable to flights
        if ('duration' in sorted[0]) {
          return sorted.sort((a: any, b: any) => {
            const aDuration = parseInt(a.duration) || 0;
            const bDuration = parseInt(b.duration) || 0;
            return aDuration - bDuration;
          });
        }
        return sorted;
      case 'departure':
        // Only applicable to flights
        if ('departureTime' in sorted[0]) {
          return sorted.sort((a: any, b: any) => 
            new Date(a.departureTime).getTime() - new Date(b.departureTime).getTime()
          );
        }
        return sorted;
      default:
        return sorted;
    }
  }, []);

  // Process results with filters and sorting
  const processedResults = useMemo(() => {
    if (!searchResults) return { flights: [], hotels: [], activities: [] };

    return {
      flights: sortItems(filterFlights(searchResults.flights || []), sortBy) as FlightOption[],
      hotels: sortItems(filterHotels(searchResults.hotels || []), sortBy) as HotelOption[],
      activities: sortItems(filterActivities(searchResults.activities || []), sortBy) as ActivityOption[]
    };
  }, [searchResults, filters, sortBy, filterFlights, filterHotels, filterActivities, sortItems]);

  const handleAddToTrip = useCallback((type: 'flight' | 'hotel' | 'activity', item: any) => {
    if (!onAddToTrip) return;

    const itineraryItem: ItineraryItem = {
      id: `${type}_${item.id}`,
      type,
      title: type === 'flight' 
        ? `${item.airline} ${item.flightNumber}` 
        : item.name,
      description: type === 'flight'
        ? `${item.origin.city} to ${item.destination.city}`
        : type === 'hotel'
        ? `${item.rating}★ hotel in ${item.location.city}`
        : item.description,
      startTime: type === 'flight' ? item.departureTime : new Date().toISOString(),
      endTime: type === 'flight' ? item.arrivalTime : undefined,
      location: type === 'flight' ? item.destination : item.location,
      price: item.price,
      status: 'planned'
    };

    onAddToTrip(itineraryItem);
  }, [onAddToTrip]);

  const handleBulkAddToTrip = useCallback(() => {
    if (!onAddToTrip) return;

    // Add all selected items to trip
    if (selectedItems.flights.length > 0) {
      processedResults.flights
        .filter(flight => selectedItems.flights.includes(flight.id))
        .forEach(flight => handleAddToTrip('flight', flight));
    }

    if (selectedItems.hotels.length > 0) {
      processedResults.hotels
        .filter(hotel => selectedItems.hotels.includes(hotel.id))
        .forEach(hotel => handleAddToTrip('hotel', hotel));
    }

    if (selectedItems.activities.length > 0) {
      processedResults.activities
        .filter(activity => selectedItems.activities.includes(activity.id))
        .forEach(activity => handleAddToTrip('activity', activity));
    }

    clearSelections();
  }, [selectedItems, processedResults, handleAddToTrip, clearSelections]);

  // Early return after all hooks are defined
  if (!sidebarOpen) {
    return null;
  }

  return (
    <div className="search-results-sidebar">
      <div className="sidebar-header">
        <h3>Search Results</h3>
        {selectedCount > 0 && (
          <div className="selection-controls">
            <span className="selected-count">{selectedCount} selected</span>
            <button 
              onClick={clearSelections}
              className="clear-selections"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Tab navigation */}
      <div className="sidebar-tabs">
        <button
          onClick={() => setActiveTab('flights')}
          className={`tab ${activeTab === 'flights' ? 'active' : ''}`}
        >
          Flights
          {processedResults.flights.length > 0 && (
            <span className="count">({processedResults.flights.length})</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('hotels')}
          className={`tab ${activeTab === 'hotels' ? 'active' : ''}`}
        >
          Hotels
          {processedResults.hotels.length > 0 && (
            <span className="count">({processedResults.hotels.length})</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('activities')}
          className={`tab ${activeTab === 'activities' ? 'active' : ''}`}
        >
          Activities
          {processedResults.activities.length > 0 && (
            <span className="count">({processedResults.activities.length})</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('trip')}
          className={`tab ${activeTab === 'trip' ? 'active' : ''}`}
        >
          Trip Plan
        </button>
      </div>

      {/* Sort and filter controls */}
      {hasResults && activeTab !== 'trip' && (
        <div className="controls-bar">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="sort-select"
          >
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="rating">Rating</option>
            {activeTab === 'flights' && (
              <>
                <option value="duration">Duration</option>
                <option value="departure">Departure Time</option>
              </>
            )}
          </select>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`filter-button ${showFilters ? 'active' : ''}`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" stroke="currentColor" strokeWidth="2" />
            </svg>
            Filters
          </button>
        </div>
      )}

      {/* Filter panel */}
      {showFilters && hasResults && activeTab !== 'trip' && (
        <div className="filter-panel">
          <div className="filter-section">
            <h4>Price Range</h4>
            <div className="price-range-inputs">
              <input
                type="number"
                min={filterOptions.minPrice}
                max={filterOptions.maxPrice}
                value={filters.priceRange.min}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange, min: Number(e.target.value) }
                }))}
                placeholder="Min"
                className="price-input"
              />
              <span>-</span>
              <input
                type="number"
                min={filterOptions.minPrice}
                max={filterOptions.maxPrice}
                value={filters.priceRange.max}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: { ...prev.priceRange, max: Number(e.target.value) }
                }))}
                placeholder="Max"
                className="price-input"
              />
            </div>
          </div>

          {(activeTab === 'hotels' || activeTab === 'activities') && (
            <div className="filter-section">
              <h4>Minimum Rating</h4>
              <div className="rating-filter">
                {[1, 2, 3, 4, 5].map(rating => (
                  <button
                    key={rating}
                    onClick={() => setFilters(prev => ({ 
                      ...prev, 
                      rating: prev.rating === rating ? 0 : rating 
                    }))}
                    className={`rating-button ${filters.rating >= rating ? 'active' : ''}`}
                  >
                    {'★'.repeat(rating)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'flights' && (
            <>
              <div className="filter-section">
                <h4>Airlines</h4>
                <div className="checkbox-group">
                  {filterOptions.airlines.map(airline => (
                    <label key={airline} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={filters.airlines.includes(airline)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFilters(prev => ({
                              ...prev,
                              airlines: [...prev.airlines, airline]
                            }));
                          } else {
                            setFilters(prev => ({
                              ...prev,
                              airlines: prev.airlines.filter(a => a !== airline)
                            }));
                          }
                        }}
                      />
                      {airline}
                    </label>
                  ))}
                </div>
              </div>

              <div className="filter-section">
                <h4>Stops</h4>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="stops"
                      checked={filters.stops === null}
                      onChange={() => setFilters(prev => ({ ...prev, stops: null }))}
                    />
                    Any
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="stops"
                      checked={filters.stops === 0}
                      onChange={() => setFilters(prev => ({ ...prev, stops: 0 }))}
                    />
                    Nonstop
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="stops"
                      checked={filters.stops === 1}
                      onChange={() => setFilters(prev => ({ ...prev, stops: 1 }))}
                    />
                    1 Stop
                  </label>
                </div>
              </div>

              <div className="filter-section">
                <h4>Departure Time</h4>
                <div className="time-filter">
                  {(['morning', 'afternoon', 'evening', 'night'] as const).map(time => (
                    <button
                      key={time}
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        departureTime: prev.departureTime === time ? null : time
                      }))}
                      className={`time-button ${filters.departureTime === time ? 'active' : ''}`}
                    >
                      {time.charAt(0).toUpperCase() + time.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {activeTab === 'hotels' && filterOptions.amenities.length > 0 && (
            <div className="filter-section">
              <h4>Amenities</h4>
              <div className="checkbox-group">
                {filterOptions.amenities.slice(0, 10).map(amenity => (
                  <label key={amenity} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={filters.amenities.includes(amenity)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters(prev => ({
                            ...prev,
                            amenities: [...prev.amenities, amenity]
                          }));
                        } else {
                          setFilters(prev => ({
                            ...prev,
                            amenities: prev.amenities.filter(a => a !== amenity)
                          }));
                        }
                      }}
                    />
                    {amenity}
                  </label>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => setFilters({
              priceRange: { min: 0, max: 10000 },
              rating: 0,
              amenities: [],
              airlines: [],
              stops: null,
              departureTime: null
            })}
            className="reset-filters-button"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* Content area */}
      <div className="sidebar-content">
        {activeTab === 'trip' ? (
          sessionId ? (
            <TripPlanPanel sessionId={sessionId} isOpen={true} />
          ) : (
            <div className="empty-state">
              <p>No session available for trip planning</p>
            </div>
          )
        ) : isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner large" />
            <p>Searching for {activeTab}...</p>
          </div>
        ) : !hasResults ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
                <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" />
              </svg>
            </div>
            <h4>No results yet</h4>
            <p>Start a conversation to see search results here</p>
          </div>
        ) : (
          <div className="results-content">
            {activeTab === 'flights' && processedResults.flights.length > 0 && (
              <div className="flights-list">
                {processedResults.flights.map((flight) => (
                  <div key={flight.id} className="result-item-wrapper">
                    <FlightCard
                      flight={flight}
                      isSelected={selectedItems.flights.includes(flight.id)}
                      onSelect={() => toggleItemSelection('flights', flight.id)}
                    />
                    {onAddToTrip && (
                      <button
                        onClick={() => handleAddToTrip('flight', flight)}
                        className="add-to-trip-button"
                        title="Add to trip"
                      >
                        ➕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'hotels' && processedResults.hotels.length > 0 && (
              <div className="hotels-list">
                {processedResults.hotels.map((hotel) => (
                  <div key={hotel.id} className="result-item-wrapper">
                    <HotelCard
                      hotel={hotel}
                      isSelected={selectedItems.hotels.includes(hotel.id)}
                      onSelect={() => toggleItemSelection('hotels', hotel.id)}
                    />
                    {onAddToTrip && (
                      <button
                        onClick={() => handleAddToTrip('hotel', hotel)}
                        className="add-to-trip-button"
                        title="Add to trip"
                      >
                        ➕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'activities' && processedResults.activities.length > 0 && (
              <div className="activities-list">
                {processedResults.activities.map((activity) => (
                  <div key={activity.id} className="result-item-wrapper">
                    <ActivityCard
                      activity={activity}
                      isSelected={selectedItems.activities.includes(activity.id)}
                      onSelect={() => toggleItemSelection('activities', activity.id)}
                      onAddToTrip={onAddToTrip ? () => handleAddToTrip('activity', activity) : undefined}
                      participants={1}
                    />
                    {onAddToTrip && (
                      <button
                        onClick={() => handleAddToTrip('activity', activity)}
                        className="add-to-trip-button"
                        title="Add to trip"
                      >
                        ➕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* No results after filtering */}
            {((activeTab === 'flights' && processedResults.flights.length === 0) ||
              (activeTab === 'hotels' && processedResults.hotels.length === 0) ||
              (activeTab === 'activities' && processedResults.activities.length === 0)) && (
              <div className="no-results">
                <p>No {activeTab} match your filters</p>
                <button 
                  onClick={() => setFilters({
                    priceRange: { min: 0, max: 10000 },
                    rating: 0,
                    amenities: [],
                    airlines: [],
                    stops: null,
                    departureTime: null
                  })}
                  className="btn-secondary"
                >
                  Reset Filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      {selectedCount > 0 && activeTab !== 'trip' && (
        <div className="sidebar-actions">
          <button 
            className="btn-primary"
            onClick={handleBulkAddToTrip}
          >
            Add to Trip ({selectedCount})
          </button>
          <button className="btn-secondary">
            Compare Selected
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchResultsSidebar;