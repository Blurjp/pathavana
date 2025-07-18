import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUnifiedSession } from '../hooks/useUnifiedSession';
import { useSidebar } from '../contexts/SidebarContext';
import { AuthGuard } from '../components/auth/AuthGuard';
import ChatInput from '../components/ChatInput';
import SearchResultsSidebar from '../components/SearchResultsSidebar';
import InteractiveMap from '../components/InteractiveMap';
import SearchProgress from '../components/search/SearchProgress';
import SmartPrompts from '../components/SmartPrompts';
import { ChatMessage, SearchResults, Location, ItineraryItem } from '../types';
import { formatDateTime, getRelativeTimeString } from '../utils/dateHelpers';
import '../styles/pages/UnifiedTravelRequest.css';
import '../styles/components/DatePicker.css';
import '../styles/components/SmartPrompts.css';

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
    syncWithServer,
    searchResults,
    isSearching
  } = useUnifiedSession(urlSessionId);

  const { sidebarOpen, toggleSidebar } = useSidebar();
  const [currentSearchResults, setCurrentSearchResults] = useState<SearchResults | undefined>();
  const [mapLocations, setMapLocations] = useState<Location[]>([]);
  const [showMap, setShowMap] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [searchType, setSearchType] = useState<'flight' | 'hotel' | 'activity' | null>(null);
  const [searchMessageId, setSearchMessageId] = useState<string | null>(null);
  const [tripPlanCreated, setTripPlanCreated] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  // Debug log for messages
  useEffect(() => {
    console.log('Messages in UnifiedTravelRequest:', messages.length, messages);
  }, [messages]);

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
      
      // Clear search status when results arrive
      setSearchType(null);
      setSearchMessageId(null);
      
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
  
  // Check for trip plan creation 
  useEffect(() => {
    const latestAssistantMessage = [...messages]
      .reverse()
      .find(msg => msg.type === 'assistant' && msg.metadata?.trip_plan_created);
    
    if (latestAssistantMessage?.metadata?.trip_plan_created && !tripPlanCreated) {
      setTripPlanCreated(true);
      
      // Auto-open sidebar to show trip plan
      if (!sidebarOpen) {
        toggleSidebar();
      }
      
      console.log('Trip plan created:', latestAssistantMessage.metadata.trip_plan);
    }
  }, [messages, tripPlanCreated, sidebarOpen, toggleSidebar]);
  
  // Track the latest user message that might trigger a search
  useEffect(() => {
    if (searchType && messages.length > 0) {
      const latestUserMessage = [...messages].reverse().find(msg => msg.type === 'user');
      if (latestUserMessage) {
        setSearchMessageId(latestUserMessage.id);
      }
    }
  }, [messages, searchType]);

  // Generate contextual suggestions based on conversation state
  const getContextualSuggestions = useCallback(() => {
    const suggestions: string[] = [];
    
    // Check if we should show static prompts instead of AI suggestions
    // Show static prompts if there are no user messages yet (only welcome message)
    const userMessageCount = messages.filter(msg => msg.type === 'user').length;
    
    if (userMessageCount === 0) {
      // Return static prompts on initial load (before any user interaction)
      return [
        "Plan a weekend trip to Paris", 
        "Find flights to Tokyo under $800",
        "Hotels in New York for next month"
      ];
    }
    
    // Check if the last AI message has suggestions
    if (messages.length > 0) {
      const lastAIMessage = [...messages].reverse().find(msg => msg.type === 'assistant');
      if (lastAIMessage?.metadata) {
        // Prioritize suggestions from the AI response
        const metadata = lastAIMessage.metadata as any;
        
        
        // Check for various suggestion sources in order of priority
        if (metadata.orchestrator_suggestions && Array.isArray(metadata.orchestrator_suggestions)) {
          suggestions.push(...metadata.orchestrator_suggestions);
        }
        if (metadata.clarifying_questions && Array.isArray(metadata.clarifying_questions)) {
          suggestions.push(...metadata.clarifying_questions);
        }
        if (metadata.suggestions && Array.isArray(metadata.suggestions)) {
          suggestions.push(...metadata.suggestions);
        }
        if (metadata.hints && Array.isArray(metadata.hints)) {
          // Convert hint objects to suggestion strings
          metadata.hints.forEach((hint: any) => {
            if (typeof hint === 'string') {
              suggestions.push(hint);
            } else if (hint.text) {
              suggestions.push(hint.text);
            }
          });
        }
        
        // Return early if we have AI-generated suggestions
        if (suggestions.length > 0) {
          return suggestions.slice(0, 5); // Limit to 5 suggestions
        }
      }
    }
    
    // Fallback to static suggestions if no AI suggestions available
    if (!context?.currentRequest && suggestions.length === 0) {
      return [
        "Plan a weekend trip to Paris", 
        "Find flights to Tokyo under $800",
        "Hotels in New York for next month"
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
  }, [context, currentSearchResults, messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const detectSearchType = (message: string): 'flight' | 'hotel' | 'activity' | null => {
    const lowerMessage = message.toLowerCase();
    if (/\b(flight|fly|flying|airfare|plane)\b/.test(lowerMessage)) return 'flight';
    if (/\b(hotel|accommodation|stay|lodging|room)\b/.test(lowerMessage)) return 'hotel';
    if (/\b(activity|activities|things to do|attractions|tours)\b/.test(lowerMessage)) return 'activity';
    return null;
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
      
      // Detect search type from message
      const detectedType = detectSearchType(content);
      if (detectedType) {
        setSearchType(detectedType);
        // Set the message ID for the next user message
        const nextMessageId = `user-${Date.now()}`;
        setSearchMessageId(nextMessageId);
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

  const handleNewChat = () => {
    // Navigate to /chat which will create a new session and redirect
    navigate('/chat');
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
                
                {/* Show search progress for user messages that triggered a search */}
                {message.type === 'user' && searchType && searchMessageId === message.id && isSearching && (
                  <SearchProgress
                    type={searchType}
                    status="searching"
                  />
                )}
                
                {/* Show search progress with results count for assistant messages */}
                {message.type === 'assistant' && message.metadata?.searchResults && (
                  <>
                    {message.metadata.searchResults.flights && (
                      <div onClick={() => !sidebarOpen && toggleSidebar()} style={{ cursor: 'pointer' }}>
                        <SearchProgress
                          type="flight"
                          status="found"
                          count={message.metadata.searchResults.flights.length}
                        />
                      </div>
                    )}
                    {message.metadata.searchResults.hotels && (
                      <div onClick={() => !sidebarOpen && toggleSidebar()} style={{ cursor: 'pointer' }}>
                        <SearchProgress
                          type="hotel"
                          status="found"
                          count={message.metadata.searchResults.hotels.length}
                        />
                      </div>
                    )}
                    {message.metadata.searchResults.activities && (
                      <div onClick={() => !sidebarOpen && toggleSidebar()} style={{ cursor: 'pointer' }}>
                        <SearchProgress
                          type="activity"
                          status="found"
                          count={message.metadata.searchResults.activities.length}
                        />
                      </div>
                    )}
                  </>
                )}
                
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

        {/* Smart prompts for date selection */}
        <SmartPrompts
          lastMessage={messages.length > 0 ? messages[messages.length - 1]?.content : ''}
          metadata={messages.length > 0 ? messages[messages.length - 1]?.metadata : undefined}
          onSendMessage={handleSendMessage}
          disabled={isMessageLoading || isStreaming || !!messageError}
        />

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
        searchResults={currentSearchResults || searchResults}
        isLoading={isSearching || isMessageLoading || isStreaming}
        onAddToTrip={handleAddToTrip}
        sessionId={sessionId}
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