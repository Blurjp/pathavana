import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedSession } from '../hooks/useUnifiedSession';
import { useSidebar } from '../contexts/SidebarContext';
import { AuthGuard } from '../components/auth/AuthGuard';
import ChatInput from '../components/ChatInput';
import SearchResultsSidebar from '../components/SearchResultsSidebar';
import { ChatMessage, SearchResults } from '../types';
import { formatDateTime, getRelativeTimeString } from '../utils/dateHelpers';

const TravelRequest: React.FC = () => {
  const navigate = useNavigate();
  
  const {
    messages,
    isMessageLoading,
    messageError,
    sendMessage,
    createNewSession,
    sessionId
  } = useUnifiedSession(undefined, true); // Force new session on initial load only

  const { sidebarOpen } = useSidebar();
  const [currentSearchResults, setCurrentSearchResults] = useState<SearchResults | undefined>();

  // Create a new session immediately on mount
  useEffect(() => {
    const initNewChat = async () => {
      // Only create if we don't have a sessionId yet
      if (!sessionId) {
        console.log('Creating new chat session...');
        const newSessionId = await createNewSession();
        if (newSessionId) {
          // Navigate to the new session URL
          navigate(`/chat/${newSessionId}`, { replace: true });
        }
      } else {
        // If we somehow have a sessionId, redirect to it
        navigate(`/chat/${sessionId}`, { replace: true });
      }
    };
    
    initNewChat();
  }, []); // Only run on mount

  // Extract search results from the latest assistant message
  useEffect(() => {
    const latestAssistantMessage = [...messages]
      .reverse()
      .find(msg => msg.type === 'assistant' && msg.metadata?.searchResults);
    
    if (latestAssistantMessage?.metadata?.searchResults) {
      setCurrentSearchResults(latestAssistantMessage.metadata.searchResults);
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage(content);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleNewChat = async () => {
    try {
      await createNewSession();
      setCurrentSearchResults(undefined);
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';

    return (
      <div
        key={message.id}
        className={`message ${message.type} ${isSystem ? 'system' : ''}`}
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
            <div className="message-text">
              {message.content && typeof message.content === 'string' 
                ? message.content.split('\n').map((line, index) => (
                    <p key={index}>{line}</p>
                  ))
                : <p>{message.content || 'No content available'}</p>
              }
            </div>
            
            {message.metadata?.suggestions && message.metadata.suggestions.length > 0 && (
              <div className="suggestions">
                <p className="suggestions-label">You might also ask:</p>
                <div className="suggestion-buttons">
                  {message.metadata.suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSendMessage(suggestion)}
                      className="suggestion-button"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
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
    <div className={`travel-request-page ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="chat-container">

        {/* Messages area */}
        <div className="messages-container">
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
              <h2>Start Planning Your Next Adventure</h2>
              <p>
                I'm here to help you find flights, hotels, and activities for your trip.
                Just tell me where you want to go!
              </p>
              <div className="example-queries">
                <h3>Try asking me:</h3>
                <ul>
                  <li>"I want to visit Paris for a week in June"</li>
                  <li>"Find me flights from New York to Tokyo under $800"</li>
                  <li>"Plan a family vacation to Disney World"</li>
                  <li>"What's the best time to visit Bali?"</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map(renderMessage)}
              
              {isMessageLoading && (
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
                    // Instead of reloading, create a new session
                    handleNewChat();
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
            isLoading={isMessageLoading}
            disabled={!!messageError}
          />
        </div>
      </div>

      {/* Search results sidebar */}
      <SearchResultsSidebar
        searchResults={currentSearchResults}
        isLoading={isMessageLoading}
        sessionId={sessionId}
      />
    </div>
  );
};

const TravelRequestWithAuth: React.FC = () => (
  <AuthGuard>
    <TravelRequest />
  </AuthGuard>
);

export default TravelRequestWithAuth;