import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useChatManager } from './useChatManager';
import { useSessionManager } from './useSessionManager';
import { useTripContext } from './useTripContext';
import { ChatMessage } from '../types';

interface UseUnifiedSessionReturn {
  sessionId: string;
  isSessionLoading: boolean;
  sessionError: string | null;
  messages: ChatMessage[];
  isMessageLoading: boolean;
  messageError: string | null;
  isStreaming: boolean;
  streamingMessage: string;
  context: any;
  isContextLoading: boolean;
  contextError: string | null;
  sendMessage: (content: string) => Promise<void>;
  createNewSession: () => Promise<void>;
  clearSession: () => Promise<void>;
  updateContext: (updates: any) => void;
  resendMessage: (messageId: string) => Promise<void>;
  deleteMessage: (messageId: string) => void;
  editMessage: (messageId: string, newContent: string) => Promise<void>;
  syncWithServer: () => Promise<void>;
}

export const useUnifiedSession = (initialSessionId?: string): UseUnifiedSessionReturn => {
  const [sessionId, setSessionId] = useState<string>(() => {
    return initialSessionId || localStorage.getItem('currentSessionId') || uuidv4();
  });

  const {
    currentSession,
    isLoading: isSessionLoading,
    error: sessionError,
    createNewSession: createSession,
    loadSession,
    deleteSession,
  } = useSessionManager();

  const {
    messages,
    isLoading: isMessageLoading,
    error: messageError,
    isStreaming,
    streamingMessage,
    sendMessage: sendChatMessage,
    clearMessages,
    resendMessage,
    deleteMessage,
    editMessage,
    syncWithServer: syncMessages,
  } = useChatManager(sessionId);

  const {
    context,
    isLoading: isContextLoading,
    error: contextError,
    updateCurrentRequest,
    clearContext,
    addToTrip,
    removeFromTrip,
    updateTrip,
    detectConflicts,
    resolveConflicts,
  } = useTripContext(sessionId);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  // Update localStorage when sessionId changes
  useEffect(() => {
    localStorage.setItem('currentSessionId', sessionId);
  }, [sessionId]);

  const initializeSession = async () => {
    try {
      // Try to load existing session first
      if (initialSessionId) {
        const loaded = await loadSession(initialSessionId);
        if (loaded) {
          setSessionId(initialSessionId);
          return;
        }
      }

      // Check if current sessionId exists
      const loaded = await loadSession(sessionId);
      if (!loaded) {
        // Create new session if current one doesn't exist
        await createNewSession();
      }
    } catch (err) {
      console.error('Failed to initialize session:', err);
      await createNewSession();
    }
  };

  const createNewSession = useCallback(async () => {
    try {
      const newSessionId = await createSession();
      if (newSessionId) {
        setSessionId(newSessionId);
        clearMessages();
        await clearContext();
        
        // Clear any pending messages
        sessionStorage.removeItem('pendingMessage');
      }
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  }, [createSession, clearMessages, clearContext]);

  const clearSession = useCallback(async () => {
    try {
      if (currentSession) {
        await deleteSession(currentSession.id);
      }
      await clearContext();
      clearMessages();
      await createNewSession();
    } catch (err) {
      console.error('Failed to clear session:', err);
    }
  }, [currentSession, deleteSession, clearContext, clearMessages, createNewSession]);

  const sendMessage = useCallback(async (content: string) => {
    try {
      await sendChatMessage(content);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  }, [sendChatMessage]);

  const updateContext = useCallback((updates: any) => {
    updateCurrentRequest(updates);
  }, [updateCurrentRequest]);

  const syncWithServer = useCallback(async () => {
    await syncMessages();
  }, [syncMessages]);

  // Enhance context with additional methods
  const enhancedContext = {
    ...context,
    addToTrip,
    removeFromTrip,
    updateTrip,
    detectConflicts,
    resolveConflicts,
  };

  return {
    sessionId,
    isSessionLoading,
    sessionError,
    messages,
    isMessageLoading,
    messageError,
    isStreaming,
    streamingMessage,
    context: enhancedContext,
    isContextLoading,
    contextError,
    sendMessage,
    createNewSession,
    clearSession,
    updateContext,
    resendMessage,
    deleteMessage,
    editMessage,
    syncWithServer,
  };
};