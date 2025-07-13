import React, { useState, useRef, useEffect, useCallback } from 'react';
import { getRequestHistory } from '../utils/sessionStorage';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  minRows?: number;
  maxRows?: number;
  onTyping?: (isTyping: boolean) => void;
  contextualSuggestions?: string[];
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  placeholder = "Where would you like to travel?",
  disabled = false,
  maxLength = 2000,
  minRows = 1,
  maxRows = 5,
  onTyping,
  contextualSuggestions = []
}) => {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Load suggestions from history when component mounts
    loadSuggestions();
    loadCommandHistory();
  }, []);

  useEffect(() => {
    // Merge contextual suggestions with history-based ones
    if (contextualSuggestions.length > 0) {
      setSuggestions(prev => {
        const combined = [...contextualSuggestions, ...prev];
        return Array.from(new Set(combined)).slice(0, 10);
      });
    }
  }, [contextualSuggestions]);

  useEffect(() => {
    // Auto-resize textarea with min/max constraints
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const minHeight = minRows * 24; // Approximate line height
      const maxHeight = maxRows * 24;
      const height = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
      textareaRef.current.style.height = `${height}px`;
      textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  }, [message, minRows, maxRows]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  const loadSuggestions = () => {
    const history = getRequestHistory();
    const uniqueQueries = Array.from(new Set(history.map(req => req.query)))
      .filter(query => query && query.trim().length > 0)
      .slice(-10) // Last 10 unique queries
      .reverse(); // Most recent first
    setSuggestions(uniqueQueries);
  };

  const loadCommandHistory = () => {
    const history = getRequestHistory();
    const commands = history
      .map(req => req.query)
      .filter(query => query && query.trim().length > 0)
      .slice(-50); // Keep last 50 commands
    setCommandHistory(commands);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled && !isComposing) {
      const trimmedMessage = message.trim();
      onSendMessage(trimmedMessage);
      
      // Add to command history
      setCommandHistory(prev => [...prev, trimmedMessage]);
      
      // Reset state
      setMessage('');
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
      setHistoryIndex(-1);
      
      // Clear typing indicator
      if (onTyping) {
        onTyping(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Enter key
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit(e);
      return;
    }

    // Handle suggestions navigation
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        return;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        return;
      } else if (e.key === 'Tab' || (e.key === 'Enter' && selectedSuggestion >= 0)) {
        if (selectedSuggestion >= 0) {
          e.preventDefault();
          setMessage(suggestions[selectedSuggestion]);
          setShowSuggestions(false);
          setSelectedSuggestion(-1);
          return;
        }
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
        setSelectedSuggestion(-1);
        return;
      }
    }

    // Handle command history navigation (when no suggestions are shown)
    if (!showSuggestions && commandHistory.length > 0) {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setMessage(commandHistory[newIndex] || '');
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const newIndex = historyIndex === -1 ? -1 : Math.min(commandHistory.length - 1, historyIndex + 1);
        setHistoryIndex(newIndex);
        if (newIndex === -1 || newIndex === commandHistory.length - 1) {
          setMessage('');
          setHistoryIndex(-1);
        } else {
          setMessage(commandHistory[newIndex] || '');
        }
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    
    // Enforce max length
    if (value.length > maxLength) {
      return;
    }
    
    setMessage(value);
    setHistoryIndex(-1); // Reset history navigation

    // Handle typing indicator
    if (onTyping) {
      onTyping(true);
      
      // Clear existing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Set new timeout to clear typing indicator
      typingTimeoutRef.current = setTimeout(() => {
        onTyping(false);
      }, 1000);
    }

    // Show suggestions when user starts typing
    if (value.length > 0) {
      const allSuggestions = [...contextualSuggestions, ...suggestions];
      const filtered = Array.from(new Set(allSuggestions))
        .filter(suggestion =>
          suggestion.toLowerCase().includes(value.toLowerCase())
        )
        .slice(0, 5); // Limit to 5 suggestions
      
      if (filtered.length > 0) {
        setSuggestions(filtered);
        setShowSuggestions(true);
        setSelectedSuggestion(-1);
      } else {
        setShowSuggestions(false);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  const handleFocus = useCallback(() => {
    if (message.length === 0 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
    textareaRef.current?.setSelectionRange(message.length, message.length);
  }, [message, suggestions]);

  const handleBlur = useCallback(() => {
    // Delay hiding suggestions to allow clicking on them
    setTimeout(() => {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }, 200);
  }, []);

  const handleCompositionStart = useCallback(() => {
    setIsComposing(true);
  }, []);

  const handleCompositionEnd = useCallback(() => {
    setIsComposing(false);
  }, []);

  const selectSuggestion = useCallback((suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
    textareaRef.current?.focus();
    
    // Move cursor to end
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.setSelectionRange(suggestion.length, suggestion.length);
      }
    }, 0);
  }, []);

  const quickPrompts = contextualSuggestions.length > 0 
    ? contextualSuggestions.slice(0, 3)
    : [
        "Plan a weekend trip to Paris",
        "Find flights to Tokyo under $800",
        "Hotels in New York for next month",
        "Family vacation to Disney World",
        "Business trip to London"
      ].slice(0, 3);

  return (
    <div className="chat-input-container">
      {/* Quick prompts - shown when input is empty */}
      {message.length === 0 && !showSuggestions && quickPrompts.length > 0 && (
        <div className="quick-prompts">
          <span className="quick-prompts-label">Try:</span>
          {quickPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => {
                setMessage(prompt);
                textareaRef.current?.focus();
              }}
              className="quick-prompt"
              disabled={disabled}
              aria-label={`Quick prompt: ${prompt}`}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="chat-textarea"
            rows={minRows}
            maxLength={maxLength}
            aria-label="Message input"
            aria-describedby={message.length > maxLength * 0.9 ? "char-count" : undefined}
            spellCheck="true"
            autoComplete="off"
            autoCorrect="on"
          />

          <button
            type="submit"
            disabled={!message.trim() || isLoading || disabled}
            className="send-button"
            aria-label="Send message"
          >
            {isLoading ? (
              <div className="loading-spinner" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        </div>

        {/* Character count */}
        {message.length > maxLength * 0.75 && (
          <div 
            id="char-count" 
            className={`character-count ${message.length > maxLength * 0.9 ? 'warning' : ''}`}
            role="status"
            aria-live="polite"
          >
            {message.length}/{maxLength}
          </div>
        )}
      </form>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div 
          ref={suggestionsRef} 
          className="suggestions-dropdown"
          role="listbox"
          aria-label="Search suggestions"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => selectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedSuggestion(index)}
              className={`suggestion-item ${
                index === selectedSuggestion ? 'selected' : ''
              }`}
              role="option"
              aria-selected={index === selectedSuggestion}
              tabIndex={-1}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
                <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" />
              </svg>
              <span className="suggestion-text">{suggestion}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatInput;