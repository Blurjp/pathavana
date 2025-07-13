import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUnifiedSession } from '../hooks/useUnifiedSession';
import { useSidebar } from '../contexts/SidebarContext';
import { AuthGuard } from '../components/auth/AuthGuard';
import ChatInput from '../components/ChatInput';
import SearchResultsSidebar from '../components/SearchResultsSidebar';
import InteractiveMap from '../components/InteractiveMap';
import { ChatMessage, SearchResults, Location, ItineraryItem } from '../types';
import { formatDateTime, getRelativeTimeString } from '../utils/dateHelpers';
import '../styles/pages/UnifiedTravelRequest.css';

const UnifiedTravelRequest: React.FC = () => {
  const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  
  const {
    sessionId,
    messages,
    isMessageLoading,
    messageError,
    isStreaming,
    streamingMessage,
    sendMessage,
    createNewSession,
    context,
    updateContext,
    resendMessage,
    deleteMessage,
    editMessage,
    syncWithServer
  } = useUnifiedSession(urlSessionId);

  const { sidebarOpen } = useSidebar();
  const [currentSearchResults, setCurrentSearchResults] = useState<SearchResults | undefined>();
  const [mapLocations, setMapLocations] = useState<Location[]>([]);
  const [showMap, setShowMap] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Update URL when sessionId changes
  useEffect(() => {
    if (sessionId && sessionId !== urlSessionId) {
      navigate(`/chat/${sessionId}`, { replace: true });
    }
  }, [sessionId, urlSessionId, navigate]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Extract search results and locations from messages
  useEffect(() => {
    const latestAssistantMessage = [...messages]
      .reverse()
      .find(msg => msg.type === 'assistant' && msg.metadata?.searchResults);
    
    if (latestAssistantMessage?.metadata?.searchResults) {
      setCurrentSearchResults(latestAssistantMessage.metadata.searchResults);
      
      // Extract locations for map
      const locations: Location[] = [];
      const results = latestAssistantMessage.metadata.searchResults;
      
      if (results.hotels) {
        results.hotels.forEach(hotel => {
          if (hotel.location.coordinates) {
            locations.push(hotel.location);
          }
        });
      }
      
      if (results.activities) {
        results.activities.forEach(activity => {
          if (activity.location?.coordinates) {
            locations.push(activity.location);
          }
        });
      }
      
      setMapLocations(locations);
    }
  }, [messages]);

  // Generate contextual suggestions based on conversation state
  const getContextualSuggestions = useCallback(() => {
    const suggestions: string[] = [];
    
    if (!context?.currentRequest) {
      return [
        "I want to plan a trip to Paris",
        "Find me flights to Tokyo next month",
        "Show me hotels in New York for this weekend"
      ];
    }

    const { destination, departureDate, returnDate, travelers, budget } = context.currentRequest;
    
    if (destination && !departureDate) {
      suggestions.push(`When would you like to visit ${destination}?`);
      suggestions.push(`Show me flights to ${destination} for next month`);
    }
    
    if (destination && departureDate && !returnDate) {
      suggestions.push(`How long would you like to stay in ${destination}?`);
      suggestions.push(`I'll stay for a week`);
    }
    
    if (!travelers) {
      suggestions.push("I'm traveling alone");
      suggestions.push("We're a group of 4 people");
    }
    
    if (!budget && destination) {
      suggestions.push(`What's the typical budget for ${destination}?`);
      suggestions.push("I have a budget of $2000");
    }
    
    if (currentSearchResults?.flights && currentSearchResults.flights.length > 0) {
      suggestions.push("Show me more flight options");
      suggestions.push("Filter flights by price");
      suggestions.push("I prefer morning departures");
    }
    
    if (currentSearchResults?.hotels && currentSearchResults.hotels.length > 0) {
      suggestions.push("Show hotels near the city center");
      suggestions.push("I need a hotel with free cancellation");
      suggestions.push("Filter hotels by rating");
    }
    
    return suggestions.slice(0, 5);
  }, [context, currentSearchResults]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (content: string) => {
    try {
      // Check for conflicts before sending
      const potentialConflicts = context?.detectConflicts?.(content) || [];
      if (potentialConflicts.length > 0) {
        setConflicts(potentialConflicts);
        setShowConflictModal(true);
        // Store the message to send after conflict resolution
        sessionStorage.setItem('pendingMessage', content);
        return;
      }
      
      await sendMessage(content);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleResolveConflict = async (resolution: 'keep_existing' | 'use_new' | 'merge') => {
    context?.resolveConflicts?.(resolution);
    setShowConflictModal(false);
    
    // Send the pending message
    const pendingMessage = sessionStorage.getItem('pendingMessage');
    if (pendingMessage) {
      sessionStorage.removeItem('pendingMessage');
      await sendMessage(pendingMessage);
    }
  };

  const handleNewChat = async () => {
    try {
      await createNewSession();
      setCurrentSearchResults(undefined);
      setMapLocations([]);
      setShowMap(false);
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  const handleEditMessage = (messageId: string, currentContent: string) => {
    setEditingMessageId(messageId);
    setEditingContent(currentContent);
  };

  const handleSaveEdit = async () => {
    if (editingMessageId && editingContent.trim()) {
      await editMessage(editingMessageId, editingContent.trim());
      setEditingMessageId(null);
      setEditingContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleAddToTrip = (item: ItineraryItem) => {
    context?.addToTrip?.(item);
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    const isEditing = editingMessageId === message.id;
    const isCurrentStreamingMessage = message.type === 'assistant' && 
      isStreaming && 
      messages[messages.length - 1]?.id === message.id;

    return (
      <div
        key={message.id}
        className={`message ${message.type} ${isSystem ? 'system' : ''} ${isEditing ? 'editing' : ''}`}
      >
        <div className="message-content">
          {!isUser && !isSystem && (
            <div className="avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          )}
          
          <div className="message-body">
            {isEditing ? (
              <div className="edit-message-form">
                <textarea
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="edit-textarea"
                  autoFocus
                />
                <div className="edit-actions">
                  <button onClick={handleSaveEdit} className="btn-primary small">
                    Save
                  </button>
                  <button onClick={handleCancelEdit} className="btn-secondary small">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="message-text">
                  {isCurrentStreamingMessage && streamingMessage ? (
                    <p>{streamingMessage}<span className="typing-cursor">|</span></p>
                  ) : (
                    message.content.split('\n').map((line, index) => (
                      <p key={index}>{line}</p>
                    ))
                  )}
                </div>
                
                {/* Show search results summary in message */}
                {message.metadata?.searchResults && (
                  <div className="search-summary">
                    <div className="summary-stats">
                      {message.metadata.searchResults.flights && (
                        <span className="stat">
                          ✈️ {message.metadata.searchResults.flights.length} flights
                        </span>
                      )}
                      {message.metadata.searchResults.hotels && (
                        <span className="stat">
                          🏨 {message.metadata.searchResults.hotels.length} hotels
                        </span>
                      )}
                      {message.metadata.searchResults.activities && (
                        <span className="stat">
                          🎭 {message.metadata.searchResults.activities.length} activities
                        </span>
                      )}
                    </div>
                    {mapLocations.length > 0 && (
                      <button
                        onClick={() => setShowMap(!showMap)}
                        className="btn-secondary small"
                      >
                        {showMap ? 'Hide Map' : 'Show on Map'}
                      </button>
                    )}
                  </div>
                )}

                {/* Inline map view */}
                {showMap && mapLocations.length > 0 && message.metadata?.searchResults && (
                  <div className="inline-map">
                    <InteractiveMap
                      locations={mapLocations}
                      height="300px"
                      onLocationSelect={(location) => {
                        console.log('Selected location:', location);
                      }}
                    />
                  </div>
                )}
                
                {message.metadata?.suggestions && message.metadata.suggestions.length > 0 && (
                  <div className="suggestions">
                    <p className="suggestions-label">You might also ask:</p>
                    <div className="suggestion-buttons">
                      {message.metadata.suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleSendMessage(suggestion)}
                          className="suggestion-button"
                          disabled={isMessageLoading || isStreaming}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
          
          {/* Message actions */}
          {isUser && !isEditing && (
            <div className="message-actions">
              <button
                onClick={() => handleEditMessage(message.id, message.content)}
                className="action-button"
                title="Edit message"
              >
                ✏️
              </button>
              <button
                onClick={() => deleteMessage(message.id)}
                className="action-button"
                title="Delete message"
              >
                🗑️
              </button>
              <button
                onClick={() => resendMessage(message.id)}
                className="action-button"
                title="Resend message"
              >
                🔄
              </button>
            </div>
          )}
        </div>
        
        <div className="message-meta">
          <span className="timestamp" title={formatDateTime(message.timestamp)}>
            {getRelativeTimeString(message.timestamp)}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className={`unified-travel-request-page ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="chat-container">
        {/* Chat header with context info */}
        <div className="chat-header">
          <div className="chat-title">
            <h1>Trip Planning Session</h1>
            {context?.currentRequest && (
              <div className="current-context">
                {context.currentRequest.destination && (
                  <span className="context-item">
                    📍 {context.currentRequest.destination}
                  </span>
                )}
                {context.currentRequest.departureDate && (
                  <span className="context-item">
                    📅 {new Date(context.currentRequest.departureDate).toLocaleDateString()}
                  </span>
                )}
                {context.currentRequest.travelers && (
                  <span className="context-item">
                    👥 {context.currentRequest.travelers} traveler{context.currentRequest.travelers !== 1 ? 's' : ''}
                  </span>
                )}
                {context.currentRequest.budget && (
                  <span className="context-item">
                    💰 ${context.currentRequest.budget}
                  </span>
                )}
              </div>
            )}
          </div>
          
          <div className="chat-actions">
            <button
              onClick={() => setShowMap(!showMap)}
              className={`btn-secondary ${showMap ? 'active' : ''}`}
              disabled={mapLocations.length === 0}
              title={mapLocations.length === 0 ? 'No locations to show' : 'Toggle map view'}
            >
              🗺️ Map
            </button>
            <button
              onClick={syncWithServer}
              className="btn-secondary"
              title="Sync with server"
            >
              🔄 Sync
            </button>
            <button
              onClick={handleNewChat}
              className="btn-secondary"
              disabled={isMessageLoading || isStreaming}
            >
              ➕ New Chat
            </button>
          </div>
        </div>

        {/* Global map view */}
        {showMap && mapLocations.length > 0 && (
          <div className="global-map">
            <div className="map-header">
              <h3>Location Overview</h3>
              <button
                onClick={() => setShowMap(false)}
                className="close-map"
              >
                ✕
              </button>
            </div>
            <InteractiveMap
              locations={mapLocations}
              height="400px"
              onLocationSelect={(location) => {
                console.log('Selected location:', location);
              }}
            />
          </div>
        )}

        {/* Messages area */}
        <div className="messages-container" ref={messagesContainerRef}>
          {messages.length === 0 ? (
            <div className="welcome-state">
              <div className="welcome-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <polyline points="3.27,6.96 12,12.01 20.73,6.96" stroke="currentColor" strokeWidth="2" />
                  <line x1="12" y1="22.08" x2="12" y2="12" stroke="currentColor" strokeWidth="2" />
                </svg>
              </div>
              <h2>Welcome to Your Trip Planning Session</h2>
              <p>
                This is a persistent session where all your travel planning context is saved.
                I'll remember your preferences and help you build the perfect trip.
              </p>
              <div className="session-benefits">
                <div className="benefit">
                  <span className="icon">💾</span>
                  <div>
                    <strong>Automatic Saving</strong>
                    <p>Your conversation is saved locally and synced with the server</p>
                  </div>
                </div>
                <div className="benefit">
                  <span className="icon">🔄</span>
                  <div>
                    <strong>Smart Context</strong>
                    <p>I remember your travel preferences and search history</p>
                  </div>
                </div>
                <div className="benefit">
                  <span className="icon">🗺️</span>
                  <div>
                    <strong>Visual Planning</strong>
                    <p>See hotels and activities on an interactive map</p>
                  </div>
                </div>
                <div className="benefit">
                  <span className="icon">🚀</span>
                  <div>
                    <strong>Real-time Updates</strong>
                    <p>Get live flight and hotel availability as we chat</p>
                  </div>
                </div>
              </div>
              <div className="session-info">
                <p className="session-id">Session ID: {sessionId}</p>
                <p className="session-hint">Share this URL to continue planning on another device</p>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map(renderMessage)}
              
              {(isMessageLoading || isStreaming) && !streamingMessage && (
                <div className="message assistant loading">
                  <div className="message-content">
                    <div className="avatar">
                      <div className="loading-spinner" />
                    </div>
                    <div className="message-body">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}

          {messageError && (
            <div className="error-message">
              <div className="error-icon">⚠️</div>
              <div className="error-content">
                <p><strong>Something went wrong</strong></p>
                <p>{messageError}</p>
                <button
                  onClick={() => {
                    // Instead of reloading, try to resend the last message or create new session
                    navigate('/chat');
                  }}
                  className="btn-secondary"
                >
                  Start New Chat
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Chat input */}
        <div className="chat-input-container">
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isMessageLoading || isStreaming}
            disabled={!!messageError}
            placeholder="Continue planning your trip..."
            contextualSuggestions={getContextualSuggestions()}
          />
        </div>
      </div>

      {/* Search results sidebar */}
      <SearchResultsSidebar
        searchResults={currentSearchResults}
        isLoading={isMessageLoading || isStreaming}
        onAddToTrip={handleAddToTrip}
      />

      {/* Conflict resolution modal */}
      {showConflictModal && (
        <div className="modal-overlay" onClick={() => setShowConflictModal(false)}>
          <div className="conflict-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Conflicting Information Detected</h3>
            <p>I noticed some differences from what we discussed earlier:</p>
            <ul className="conflict-list">
              {conflicts.map((conflict, index) => (
                <li key={index}>{conflict}</li>
              ))}
            </ul>
            <p>How would you like to proceed?</p>
            <div className="conflict-actions">
              <button
                onClick={() => handleResolveConflict('keep_existing')}
                className="btn-secondary"
              >
                Keep Current Plan
              </button>
              <button
                onClick={() => handleResolveConflict('use_new')}
                className="btn-primary"
              >
                Use New Information
              </button>
              <button
                onClick={() => handleResolveConflict('merge')}
                className="btn-secondary"
              >
                Merge Both
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const UnifiedTravelRequestWithAuth: React.FC = () => (
  <AuthGuard>
    <UnifiedTravelRequest />
  </AuthGuard>
);

export default UnifiedTravelRequestWithAuth;