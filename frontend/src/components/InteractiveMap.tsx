import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Location, FlightOption, HotelOption, ActivityOption } from '../types';
import './InteractiveMap.css';

interface MapLocation extends Location {
  id: string;
  type: 'destination' | 'hotel' | 'activity' | 'flight-origin' | 'flight-destination';
  data?: FlightOption | HotelOption | ActivityOption;
}

interface RouteInfo {
  id: string;
  origin: MapLocation;
  destination: MapLocation;
  type: 'flight' | 'transport';
  data?: FlightOption;
}

interface InteractiveMapProps {
  locations?: Location[];
  hotels?: HotelOption[];
  activities?: ActivityOption[];
  flights?: FlightOption[];
  routes?: RouteInfo[];
  center?: { lat: number; lng: number };
  zoom?: number;
  height?: string;
  className?: string;
  showControls?: boolean;
  showHeatmap?: boolean;
  onLocationSelect?: (location: MapLocation) => void;
  onRouteSelect?: (route: RouteInfo) => void;
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  locations = [],
  hotels = [],
  activities = [],
  flights = [],
  routes = [],
  center = { lat: 40.7128, lng: -74.0060 }, // Default to NYC
  zoom = 10,
  height = '400px',
  className = '',
  showControls = true,
  showHeatmap = false,
  onLocationSelect,
  onRouteSelect
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [markers, setMarkers] = useState<any[]>([]);
  const [polylines, setPolylines] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'hotels' | 'activities' | 'flights'>('all');
  const [showTraffic, setShowTraffic] = useState(false);
  const [showHeatmapState, setShowHeatmap] = useState(showHeatmap || false);
  const [mapType, setMapType] = useState<'roadmap' | 'satellite' | 'hybrid' | 'terrain'>('roadmap');

  // Helper functions
  const createMapLocations = useCallback((): MapLocation[] => {
    const mapLocations: MapLocation[] = [];

    // Add regular locations
    locations.forEach((location, index) => {
      mapLocations.push({
        ...location,
        id: `location-${index}`,
        type: 'destination'
      });
    });

    // Add hotels
    hotels.forEach((hotel, index) => {
      mapLocations.push({
        ...hotel.location,
        id: `hotel-${hotel.id || index}`,
        type: 'hotel',
        data: hotel
      });
    });

    // Add activities
    activities.forEach((activity, index) => {
      mapLocations.push({
        ...activity.location,
        id: `activity-${activity.id || index}`,
        type: 'activity',
        data: activity
      });
    });

    // Add flight origins and destinations
    flights.forEach((flight, index) => {
      mapLocations.push({
        address: flight.origin.name,
        city: flight.origin.city,
        country: flight.origin.country,
        coordinates: flight.origin.coordinates,
        id: `flight-origin-${flight.id || index}`,
        type: 'flight-origin',
        data: flight
      });
      
      mapLocations.push({
        address: flight.destination.name,
        city: flight.destination.city,
        country: flight.destination.country,
        coordinates: flight.destination.coordinates,
        id: `flight-destination-${flight.id || index}`,
        type: 'flight-destination',
        data: flight
      });
    });

    return mapLocations;
  }, [locations, hotels, activities, flights]);

  const getMarkerIcon = (type: MapLocation['type']): string => {
    const iconMap = {
      'destination': '📍',
      'hotel': '🏨',
      'activity': '🎯',
      'flight-origin': '✈️',
      'flight-destination': '🛬'
    };
    return iconMap[type] || '📍';
  };

  const getMarkerColor = (type: MapLocation['type']): string => {
    const colorMap = {
      'destination': '#2563eb',
      'hotel': '#059669',
      'activity': '#dc2626',
      'flight-origin': '#7c3aed',
      'flight-destination': '#ea580c'
    };
    return colorMap[type] || '#2563eb';
  };

  const shouldShowMarker = (type: MapLocation['type']): boolean => {
    if (activeFilter === 'all') return true;
    
    switch (activeFilter) {
      case 'hotels':
        return type === 'hotel';
      case 'activities':
        return type === 'activity';
      case 'flights':
        return type === 'flight-origin' || type === 'flight-destination';
      default:
        return true;
    }
  };

  // Load Google Maps script
  useEffect(() => {
    const loadGoogleMaps = () => {
      if (window.google && window.google.maps) {
        setIsLoaded(true);
        return;
      }

      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}&libraries=places,visualization`;
      script.async = true;
      script.defer = true;
      script.onload = () => setIsLoaded(true);
      script.onerror = () => setError('Failed to load Google Maps');
      document.head.appendChild(script);
    };

    if (!process.env.REACT_APP_GOOGLE_MAPS_API_KEY) {
      setError('Google Maps API key not configured');
      return;
    }

    loadGoogleMaps();
  }, []);

  // Initialize map
  useEffect(() => {
    if (!isLoaded || !mapRef.current || map) return;

    try {
      const googleMap = new window.google.maps.Map(mapRef.current, {
        center,
        zoom,
        mapTypeId: mapType,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        scaleControl: true,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          },
          {
            featureType: 'transit',
            elementType: 'labels',
            stylers: [{ visibility: 'simplified' }]
          }
        ]
      });

      // Add traffic layer
      const trafficLayer = new window.google.maps.TrafficLayer();
      if (showTraffic) {
        trafficLayer.setMap(googleMap);
      }

      setMap(googleMap);
    } catch (err) {
      setError('Failed to initialize map');
    }
  }, [isLoaded, center, zoom, mapType, showTraffic, map]);

  // Update markers and routes when data changes
  useEffect(() => {
    if (!map || !window.google) return;

    // Clear existing markers and routes
    markers.forEach(marker => marker.setMap(null));
    polylines.forEach(polyline => polyline.setMap(null));
    if (heatmap) heatmap.setMap(null);

    const mapLocations = createMapLocations();
    
    // Create new markers
    const newMarkers = mapLocations
      .filter(location => location.coordinates && shouldShowMarker(location.type))
      .map((location) => {
        const icon = {
          url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
            <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
              <circle cx="16" cy="16" r="12" fill="${getMarkerColor(location.type)}" stroke="white" stroke-width="2"/>
              <text x="16" y="20" text-anchor="middle" font-size="12" fill="white">${getMarkerIcon(location.type)}</text>
            </svg>
          `)}`,
          scaledSize: new window.google.maps.Size(32, 32),
          anchor: new window.google.maps.Point(16, 16)
        };

        const marker = new window.google.maps.Marker({
          position: location.coordinates!,
          map,
          title: location.address,
          icon,
          animation: window.google.maps.Animation.DROP
        });

        // Create enhanced info window content
        const getInfoWindowContent = (loc: MapLocation): string => {
          let content = `
            <div class="map-info-window">
              <div class="info-header">
                <span class="info-icon">${getMarkerIcon(loc.type)}</span>
                <h4>${loc.type === 'hotel' && loc.data ? (loc.data as HotelOption).name : 
                     loc.type === 'activity' && loc.data ? (loc.data as ActivityOption).name : 
                     loc.address}</h4>
              </div>
              <p class="info-location">${loc.city}, ${loc.country}</p>
          `;

          if (loc.data) {
            const data = loc.data;
            if (loc.type === 'hotel') {
              const hotel = data as HotelOption;
              content += `
                <div class="info-details">
                  <div class="rating">★ ${hotel.rating}/5</div>
                  <div class="price">${hotel.price.displayPrice}/night</div>
                </div>
              `;
            } else if (loc.type === 'activity') {
              const activity = data as ActivityOption;
              content += `
                <div class="info-details">
                  <div class="type">${activity.type}</div>
                  <div class="price">${activity.price.displayPrice}</div>
                  ${activity.duration ? `<div class="duration">${activity.duration}</div>` : ''}
                </div>
              `;
            } else if (loc.type.includes('flight')) {
              const flight = data as FlightOption;
              content += `
                <div class="info-details">
                  <div class="airline">${flight.airline} ${flight.flightNumber}</div>
                  <div class="price">${flight.price.displayPrice}</div>
                </div>
              `;
            }
          }

          content += `</div>`;
          return content;
        };

        const infoWindow = new window.google.maps.InfoWindow({
          content: getInfoWindowContent(location)
        });

        // Add click listener
        marker.addListener('click', () => {
          infoWindow.open(map, marker);
          if (onLocationSelect) {
            onLocationSelect(location);
          }
        });

        return { marker, location };
      });

    setMarkers(newMarkers.map(({ marker }) => marker));

    // Create routes for flights
    const newPolylines: any[] = [];
    flights.forEach((flight) => {
      if (flight.origin.coordinates && flight.destination.coordinates) {
        const flightPath = new window.google.maps.Polyline({
          path: [flight.origin.coordinates, flight.destination.coordinates],
          geodesic: true,
          strokeColor: '#7c3aed',
          strokeOpacity: 0.8,
          strokeWeight: 3,
          icons: [{
            icon: {
              path: window.google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
              scale: 4,
              strokeColor: '#7c3aed'
            },
            offset: '100%'
          }]
        });

        flightPath.setMap(map);
        
        flightPath.addListener('click', () => {
          if (onRouteSelect) {
            const routeInfo: RouteInfo = {
              id: flight.id,
              origin: {
                ...flight.origin,
                address: `${flight.origin.name}, ${flight.origin.city}, ${flight.origin.country}`,
                id: `flight-origin-${flight.id}`,
                type: 'flight-origin'
              },
              destination: {
                ...flight.destination,
                address: `${flight.destination.name}, ${flight.destination.city}, ${flight.destination.country}`,
                id: `flight-destination-${flight.id}`,
                type: 'flight-destination'
              },
              type: 'flight',
              data: flight
            };
            onRouteSelect(routeInfo);
          }
        });

        newPolylines.push(flightPath);
      }
    });

    setPolylines(newPolylines);

    // Create heatmap if enabled
    if (showHeatmapState && mapLocations.length > 0) {
      const heatmapData = mapLocations
        .filter(loc => loc.coordinates)
        .map(loc => new window.google.maps.LatLng(loc.coordinates!.lat, loc.coordinates!.lng));

      const heatmapLayer = new window.google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        radius: 20,
        opacity: 0.6
      });

      heatmapLayer.setMap(map);
      setHeatmap(heatmapLayer);
    }

    // Adjust map bounds to fit all visible markers
    const visibleMarkers = newMarkers.filter(({ location }) => shouldShowMarker(location.type));
    if (visibleMarkers.length > 1) {
      const bounds = new window.google.maps.LatLngBounds();
      visibleMarkers.forEach(({ marker }) => {
        bounds.extend(marker.getPosition()!);
      });
      map.fitBounds(bounds);
    } else if (visibleMarkers.length === 1) {
      map.setCenter(visibleMarkers[0].marker.getPosition()!);
      map.setZoom(15);
    }
  }, [map, createMapLocations, activeFilter, showHeatmapState, onLocationSelect, onRouteSelect, flights]);

  // Control handlers
  const handleFitBounds = () => {
    if (!map) return;
    
    const mapLocations = createMapLocations().filter(loc => 
      loc.coordinates && shouldShowMarker(loc.type)
    );
    
    if (mapLocations.length > 1) {
      const bounds = new window.google.maps.LatLngBounds();
      mapLocations.forEach(location => {
        if (location.coordinates) {
          bounds.extend(location.coordinates);
        }
      });
      map.fitBounds(bounds);
    }
  };

  const handleResetMap = () => {
    if (map) {
      map.setCenter(center);
      map.setZoom(zoom);
    }
  };

  // Fallback map component (when Google Maps is not available)
  const FallbackMap: React.FC = () => (
    <div className="fallback-map">
      <div className="fallback-content">
        <div className="map-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <path
              d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"
              stroke="currentColor"
              strokeWidth="2"
            />
            <circle cx="12" cy="10" r="3" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>
        <h4>Map View</h4>
        {error ? (
          <p className="error-message">{error}</p>
        ) : (
          <p>Loading interactive map...</p>
        )}
        {(locations.length > 0 || hotels.length > 0 || activities.length > 0) && (
          <div className="location-list">
            <h5>Locations:</h5>
            <ul>
              {locations.map((location, index) => (
                <li key={`location-${index}`}>
                  <strong>{location.address}</strong>
                  <br />
                  {location.city}, {location.country}
                </li>
              ))}
              {hotels.map((hotel, index) => (
                <li key={`hotel-${index}`}>
                  <strong>🏨 {hotel.name}</strong>
                  <br />
                  {hotel.location.city}, {hotel.location.country}
                </li>
              ))}
              {activities.map((activity, index) => (
                <li key={`activity-${index}`}>
                  <strong>🎯 {activity.name}</strong>
                  <br />
                  {activity.location.city}, {activity.location.country}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  if (error || !isLoaded) {
    return (
      <div className={`interactive-map ${className}`} style={{ height }}>
        <FallbackMap />
      </div>
    );
  }

  const mapLocations = createMapLocations();
  const hasData = mapLocations.length > 0;

  return (
    <div className={`interactive-map ${className}`} style={{ height }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
      
      {/* Map Controls */}
      {showControls && hasData && (
        <div className="map-controls">
          <div className="control-group primary-controls">
            <button
              onClick={handleFitBounds}
              className="map-control-button"
              title="Fit all visible locations"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
            
            <button
              onClick={handleResetMap}
              className="map-control-button"
              title="Reset map view"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" stroke="currentColor" strokeWidth="2"/>
                <path d="M21 3v5h-5" stroke="currentColor" strokeWidth="2"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" stroke="currentColor" strokeWidth="2"/>
                <path d="M8 16l-5-5 5-5" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </button>
          </div>

          {/* Filter Controls */}
          <div className="control-group filter-controls">
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value as any)}
              className="filter-select"
              title="Filter locations"
            >
              <option value="all">All ({mapLocations.length})</option>
              <option value="hotels">Hotels ({hotels.length})</option>
              <option value="activities">Activities ({activities.length})</option>
              <option value="flights">Flights ({flights.length})</option>
            </select>
          </div>

          {/* Map Type Controls */}
          <div className="control-group map-type-controls">
            <select
              value={mapType}
              onChange={(e) => setMapType(e.target.value as any)}
              className="map-type-select"
              title="Change map type"
            >
              <option value="roadmap">Road</option>
              <option value="satellite">Satellite</option>
              <option value="hybrid">Hybrid</option>
              <option value="terrain">Terrain</option>
            </select>
          </div>

          {/* Toggle Controls */}
          <div className="control-group toggle-controls">
            <button
              onClick={() => setShowTraffic(!showTraffic)}
              className={`map-control-button ${showTraffic ? 'active' : ''}`}
              title="Toggle traffic layer"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="3" fill={showTraffic ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2"/>
                <path d="M12 1v6m0 6v6" stroke="currentColor" strokeWidth="2"/>
                <path d="M9 7V1H4v20h5v-6" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </button>
            
            <button
              onClick={() => setShowHeatmap(!showHeatmapState)}
              className={`map-control-button ${showHeatmapState ? 'active' : ''}`}
              title="Toggle heatmap"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M2 12h20" stroke="currentColor" strokeWidth="2"/>
                <path d="M2 8h20" stroke="currentColor" strokeWidth="2"/>
                <path d="M2 16h20" stroke="currentColor" strokeWidth="2"/>
                <circle cx="8" cy="12" r="2" fill={showHeatmapState ? 'currentColor' : 'none'} stroke="currentColor"/>
                <circle cx="16" cy="8" r="2" fill={showHeatmapState ? 'currentColor' : 'none'} stroke="currentColor"/>
                <circle cx="12" cy="16" r="2" fill={showHeatmapState ? 'currentColor' : 'none'} stroke="currentColor"/>
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Legend */}
      {showControls && hasData && (
        <div className="map-legend">
          <h6>Legend</h6>
          <div className="legend-items">
            {hotels.length > 0 && (
              <div className="legend-item">
                <span className="legend-marker" style={{ backgroundColor: getMarkerColor('hotel') }}>🏨</span>
                <span>Hotels</span>
              </div>
            )}
            {activities.length > 0 && (
              <div className="legend-item">
                <span className="legend-marker" style={{ backgroundColor: getMarkerColor('activity') }}>🎯</span>
                <span>Activities</span>
              </div>
            )}
            {flights.length > 0 && (
              <div className="legend-item">
                <span className="legend-marker" style={{ backgroundColor: getMarkerColor('flight-origin') }}>✈️</span>
                <span>Flights</span>
              </div>
            )}
            {locations.length > 0 && (
              <div className="legend-item">
                <span className="legend-marker" style={{ backgroundColor: getMarkerColor('destination') }}>📍</span>
                <span>Destinations</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveMap;