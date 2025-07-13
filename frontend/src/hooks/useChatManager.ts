import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage, ChatResponse, TravelContext } from '../types';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { apiClient } from '../services/api';
import { v4 as uuidv4 } from 'uuid';
import { saveMessageHistory, getMessageHistory } from '../utils/sessionStorage';

interface UseChatManagerReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;
  streamingMessage: string;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  resendMessage: (messageId: string) => Promise<void>;
  deleteMessage: (messageId: string) => void;
  editMessage: (messageId: string, newContent: string) => Promise<void>;
  getMessageHistory: () => ChatMessage[];
  syncWithServer: () => Promise<void>;
}

export const useChatManager = (sessionId?: string): UseChatManagerReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastSyncRef = useRef<number>(Date.now());

  // Load message history when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadMessageHistory(sessionId);
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [sessionId]);

  // Auto-save messages to localStorage
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      saveMessageHistory(sessionId, messages);
    }
  }, [sessionId, messages]);

  // Periodic sync with server
  useEffect(() => {
    if (!sessionId) return;

    const syncInterval = setInterval(() => {
      const timeSinceLastSync = Date.now() - lastSyncRef.current;
      if (timeSinceLastSync > 60000) { // Sync every minute
        syncWithServer();
      }
    }, 10000); // Check every 10 seconds

    return () => clearInterval(syncInterval);
  }, [sessionId]);

  const loadMessageHistory = async (sessionId: string) => {
    try {
      // First try to load from localStorage for instant display
      const localMessages = getMessageHistory(sessionId);
      if (localMessages.length > 0) {
        setMessages(localMessages);
      }

      // Then sync with server
      const response = await unifiedTravelApi.getSession(sessionId);
      if (response.success && response.data) {
        const serverMessages = response.data.messages || [];
        
        // Merge messages, preferring server data for conflicts
        const mergedMessages = mergeMessages(localMessages, serverMessages);
        setMessages(mergedMessages);
        
        // Update local storage with merged data
        saveMessageHistory(sessionId, mergedMessages);
      }
    } catch (err) {
      console.error('Failed to load message history:', err);
      // Fall back to local messages if server fails
      const localMessages = getMessageHistory(sessionId);
      if (localMessages.length > 0) {
        setMessages(localMessages);
      }
    }
  };

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || isStreaming) return;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const userMessage: ChatMessage = {
      id: uuidv4(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setStreamingMessage('');

    try {
      abortControllerRef.current = new AbortController();
      
      // Check if streaming is supported
      const supportsStreaming = 'EventSource' in window;
      
      if (supportsStreaming && sessionId) {
        // Use SSE for streaming responses
        setIsStreaming(true);
        const assistantMessageId = uuidv4();
        const assistantMessage: ChatMessage = {
          id: assistantMessageId,
          type: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          metadata: {},
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // Create EventSource for streaming
        const url = `${process.env.REACT_APP_API_BASE_URL}/api/travel/sessions/${sessionId}/chat/stream`;
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;
        
        let accumulatedContent = '';
        
        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'content') {
            accumulatedContent += data.content;
            setStreamingMessage(accumulatedContent);
            
            // Update the assistant message
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: accumulatedContent }
                : msg
            ));
          } else if (data.type === 'metadata') {
            // Update metadata when received
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, metadata: data.metadata }
                : msg
            ));
          } else if (data.type === 'done') {
            setIsStreaming(false);
            setStreamingMessage('');
            eventSource.close();
          }
        };
        
        eventSource.onerror = (error) => {
          console.error('SSE error:', error);
          setIsStreaming(false);
          setStreamingMessage('');
          eventSource.close();
          
          // Fall back to regular API call
          sendMessageNonStreaming(content, sessionId);
        };
        
        // Send the actual message
        await apiClient.post(`/api/travel/sessions/${sessionId}/chat`, {
          message: content,
          stream: true
        });
        
      } else {
        // Fall back to non-streaming API
        await sendMessageNonStreaming(content, sessionId);
      }
      
      lastSyncRef.current = Date.now();
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to send message');
        
        // Add error message to chat
        const errorMessage: ChatMessage = {
          id: uuidv4(),
          type: 'system',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [sessionId, isLoading, isStreaming]);

  const sendMessageNonStreaming = async (content: string, sessionId?: string) => {
    const response = await unifiedTravelApi.sendChatMessage(content, sessionId);

    if (response.success && response.data) {
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          searchResults: response.data.searchResults,
          suggestions: response.data.suggestions,
          context: response.data.context,
        },
      };

      setMessages(prev => [...prev, assistantMessage]);
    } else {
      throw new Error(response.error || 'Failed to send message');
    }
  };

  const resendMessage = useCallback(async (messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.type === 'user') {
      // Remove the message and any subsequent messages
      const messageIndex = messages.findIndex(m => m.id === messageId);
      setMessages(prev => prev.slice(0, messageIndex));
      
      // Resend the message
      await sendMessage(message.content);
    }
  }, [messages, sendMessage]);

  const deleteMessage = useCallback((messageId: string) => {
    setMessages(prev => {
      const index = prev.findIndex(m => m.id === messageId);
      if (index === -1) return prev;
      
      // If deleting a user message, also remove subsequent assistant message
      const message = prev[index];
      if (message.type === 'user' && index < prev.length - 1) {
        const nextMessage = prev[index + 1];
        if (nextMessage.type === 'assistant') {
          return prev.filter((_, i) => i !== index && i !== index + 1);
        }
      }
      
      return prev.filter(m => m.id !== messageId);
    });
  }, []);

  const editMessage = useCallback(async (messageId: string, newContent: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.type === 'user') {
      // Update the message content
      setMessages(prev => prev.map(m => 
        m.id === messageId 
          ? { ...m, content: newContent, timestamp: new Date().toISOString() }
          : m
      ));
      
      // Find and remove any subsequent assistant messages
      const messageIndex = messages.findIndex(m => m.id === messageId);
      if (messageIndex < messages.length - 1) {
        setMessages(prev => prev.slice(0, messageIndex + 1));
      }
      
      // Send the edited message
      await sendMessage(newContent);
    }
  }, [messages, sendMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setStreamingMessage('');
    setIsStreaming(false);
    
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Clear from localStorage
    if (sessionId) {
      saveMessageHistory(sessionId, []);
    }
  }, [sessionId]);

  const getChatHistory = useCallback(() => {
    return messages.filter(m => m.type !== 'system');
  }, [messages]);

  const syncWithServer = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const response = await unifiedTravelApi.updateSession(sessionId, {
        messages,
        updatedAt: new Date().toISOString()
      } as any);
      
      if (response.success) {
        lastSyncRef.current = Date.now();
      }
    } catch (err) {
      console.error('Failed to sync with server:', err);
    }
  }, [sessionId, messages]);

  return {
    messages,
    isLoading,
    error,
    isStreaming,
    streamingMessage,
    sendMessage,
    clearMessages,
    resendMessage,
    deleteMessage,
    editMessage,
    getMessageHistory: getChatHistory,
    syncWithServer,
  };
};

// Helper function to merge messages from different sources
function mergeMessages(local: ChatMessage[], server: ChatMessage[]): ChatMessage[] {
  const messageMap = new Map<string, ChatMessage>();
  
  // Add server messages first (they take precedence)
  server.forEach(msg => messageMap.set(msg.id, msg));
  
  // Add local messages that don't exist on server
  local.forEach(msg => {
    if (!messageMap.has(msg.id)) {
      messageMap.set(msg.id, msg);
    }
  });
  
  // Sort by timestamp
  return Array.from(messageMap.values()).sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
}