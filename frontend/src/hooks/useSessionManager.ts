import { useState, useEffect, useCallback } from 'react';
import { TravelSession } from '../types';
import { unifiedTravelApi } from '../services/unifiedTravelApi';
import { getStoredSession, storeSession, clearStoredSession } from '../utils/sessionStorage';

interface UseSessionManagerReturn {
  currentSession: TravelSession | null;
  isLoading: boolean;
  error: string | null;
  createNewSession: () => Promise<string | null>;
  loadSession: (sessionId: string) => Promise<boolean>;
  updateSession: (updates: Partial<TravelSession>) => Promise<boolean>;
  deleteSession: (sessionId: string) => Promise<boolean>;
  getCurrentSessionId: () => string | null;
}

export const useSessionManager = (): UseSessionManagerReturn => {
  const [currentSession, setCurrentSession] = useState<TravelSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing session on mount
  useEffect(() => {
    loadExistingSession();
  }, []);

  const loadExistingSession = async () => {
    try {
      const storedSession = getStoredSession();
      if (storedSession) {
        const success = await loadSession(storedSession.sessionId);
        if (!success) {
          // If stored session is invalid, clear it
          clearStoredSession();
        }
      }
    } catch (err) {
      console.error('Failed to load existing session:', err);
      clearStoredSession();
    }
  };

  const createNewSession = useCallback(async (): Promise<string | null> => {
    setIsLoading(true);
    setError(null);

    try {
      // Create an empty session without initial message
      const response = await unifiedTravelApi.createEmptySession();
      
      if (response.success && response.data) {
        const sessionId = response.data.session_id;
        // Create welcome message for empty session
        const welcomeMessage = "Hi! I'm your AI travel assistant. Tell me about your dream trip and I'll help you plan it!";
        const initialMessages = [{
          id: `msg-${Date.now()}-1`,
          content: welcomeMessage,
          type: 'assistant' as const,
          timestamp: new Date().toISOString(),
        }];
        
        // Create initial session object
        const newSession: TravelSession = {
          id: sessionId,
          messages: initialMessages,
          context: {
            searchHistory: [],
            selectedOptions: {
              flights: [],
              hotels: [],
              activities: [],
            },
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          status: 'active',
        };

        setCurrentSession(newSession);
        storeSession({ sessionId, timestamp: new Date().toISOString() });
        
        // Store the session in localStorage for the chat manager to pick up
        localStorage.setItem(`travel_session_${sessionId}`, JSON.stringify(newSession));
        
        // Also save the initial messages to the message history
        if (initialMessages.length > 0) {
          const messageHistoryKey = `pathavana_messages_${sessionId}`;
          localStorage.setItem(messageHistoryKey, JSON.stringify(initialMessages));
          console.log('Saved initial messages to localStorage:', initialMessages.length, 'messages for session', sessionId);
        }
        
        return sessionId;
      } else {
        throw new Error(response.error || 'Failed to create session');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create session');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await unifiedTravelApi.getSession(sessionId);
      
      if (response.success && response.data) {
        setCurrentSession(response.data);
        storeSession({ sessionId, timestamp: new Date().toISOString() });
        return true;
      } else {
        throw new Error(response.error || 'Session not found');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load session');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateSession = useCallback(async (updates: Partial<TravelSession>): Promise<boolean> => {
    if (!currentSession) return false;

    try {
      const response = await unifiedTravelApi.updateSession(currentSession.id, {
        ...updates,
        updatedAt: new Date().toISOString(),
      });
      
      if (response.success && response.data) {
        setCurrentSession(response.data);
        return true;
      } else {
        throw new Error(response.error || 'Failed to update session');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update session');
      return false;
    }
  }, [currentSession]);

  const deleteSession = useCallback(async (sessionId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await unifiedTravelApi.deleteSession(sessionId);
      
      if (response.success) {
        // If deleting current session, clear it
        if (currentSession?.id === sessionId) {
          setCurrentSession(null);
          clearStoredSession();
        }
        return true;
      } else {
        throw new Error(response.error || 'Failed to delete session');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete session');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [currentSession]);

  const getCurrentSessionId = useCallback((): string | null => {
    return currentSession?.id || null;
  }, [currentSession]);

  return {
    currentSession,
    isLoading,
    error,
    createNewSession,
    loadSession,
    updateSession,
    deleteSession,
    getCurrentSessionId,
  };
};