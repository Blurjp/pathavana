// Browser storage utilities for session management

import { ChatMessage } from '../types';

interface StoredSession {
  sessionId: string;
  timestamp: string;
}

interface StoredTravelRequest {
  query: string;
  origin?: string;
  destination?: string;
  departureDate?: string;
  returnDate?: string;
  travelers: number;
  timestamp: string;
}

const SESSION_STORAGE_KEY = 'pathavana_session';
const REQUEST_HISTORY_KEY = 'pathavana_request_history';
const USER_PREFERENCES_KEY = 'pathavana_user_preferences';
const SEARCH_CACHE_KEY = 'pathavana_search_cache';
const MESSAGE_HISTORY_KEY_PREFIX = 'pathavana_messages_';

export const storeSession = (session: StoredSession): void => {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  } catch (error) {
    console.error('Failed to store session:', error);
  }
};

export const getStoredSession = (): StoredSession | null => {
  try {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    if (stored) {
      const session = JSON.parse(stored);
      // Check if session is not too old (24 hours)
      const sessionTime = new Date(session.timestamp).getTime();
      const now = new Date().getTime();
      const hoursDiff = (now - sessionTime) / (1000 * 60 * 60);
      
      if (hoursDiff < 24) {
        return session;
      } else {
        // Remove expired session
        clearStoredSession();
      }
    }
  } catch (error) {
    console.error('Failed to get stored session:', error);
  }
  return null;
};

export const clearStoredSession = (): void => {
  try {
    localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear stored session:', error);
  }
};

export const storeRequestHistory = (requests: StoredTravelRequest[]): void => {
  try {
    // Keep only last 50 requests
    const trimmed = requests.slice(-50);
    localStorage.setItem(REQUEST_HISTORY_KEY, JSON.stringify(trimmed));
  } catch (error) {
    console.error('Failed to store request history:', error);
  }
};

export const getRequestHistory = (): StoredTravelRequest[] => {
  try {
    const stored = localStorage.getItem(REQUEST_HISTORY_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to get request history:', error);
  }
  return [];
};

export const addToRequestHistory = (request: StoredTravelRequest): void => {
  const history = getRequestHistory();
  history.push({
    ...request,
    timestamp: new Date().toISOString()
  });
  storeRequestHistory(history);
};

export const clearRequestHistory = (): void => {
  try {
    localStorage.removeItem(REQUEST_HISTORY_KEY);
  } catch (error) {
    console.error('Failed to clear request history:', error);
  }
};

export const storeUserPreferences = (preferences: any): void => {
  try {
    localStorage.setItem(USER_PREFERENCES_KEY, JSON.stringify(preferences));
  } catch (error) {
    console.error('Failed to store user preferences:', error);
  }
};

export const getUserPreferences = (): any => {
  try {
    const stored = localStorage.getItem(USER_PREFERENCES_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to get user preferences:', error);
  }
  return null;
};

export const clearUserPreferences = (): void => {
  try {
    localStorage.removeItem(USER_PREFERENCES_KEY);
  } catch (error) {
    console.error('Failed to clear user preferences:', error);
  }
};

// Search result caching
interface CacheEntry {
  key: string;
  data: any;
  timestamp: string;
  ttl: number; // Time to live in milliseconds
}

export const cacheSearchResults = (
  key: string, 
  data: any, 
  ttlMinutes: number = 30
): void => {
  try {
    const cache = getSearchCache();
    const entry: CacheEntry = {
      key,
      data,
      timestamp: new Date().toISOString(),
      ttl: ttlMinutes * 60 * 1000
    };
    
    cache[key] = entry;
    
    // Clean expired entries
    const now = new Date().getTime();
    Object.keys(cache).forEach(cacheKey => {
      const entryTime = new Date(cache[cacheKey].timestamp).getTime();
      if (now - entryTime > cache[cacheKey].ttl) {
        delete cache[cacheKey];
      }
    });
    
    localStorage.setItem(SEARCH_CACHE_KEY, JSON.stringify(cache));
  } catch (error) {
    console.error('Failed to cache search results:', error);
  }
};

export const getCachedSearchResults = (key: string): any | null => {
  try {
    const cache = getSearchCache();
    const entry = cache[key];
    
    if (entry) {
      const now = new Date().getTime();
      const entryTime = new Date(entry.timestamp).getTime();
      
      if (now - entryTime < entry.ttl) {
        return entry.data;
      } else {
        // Entry expired, remove it
        delete cache[key];
        localStorage.setItem(SEARCH_CACHE_KEY, JSON.stringify(cache));
      }
    }
  } catch (error) {
    console.error('Failed to get cached search results:', error);
  }
  return null;
};

const getSearchCache = (): { [key: string]: CacheEntry } => {
  try {
    const stored = localStorage.getItem(SEARCH_CACHE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to get search cache:', error);
  }
  return {};
};

export const clearSearchCache = (): void => {
  try {
    localStorage.removeItem(SEARCH_CACHE_KEY);
  } catch (error) {
    console.error('Failed to clear search cache:', error);
  }
};

// Message history functions
export const saveMessageHistory = (sessionId: string, messages: ChatMessage[]): void => {
  try {
    const key = `${MESSAGE_HISTORY_KEY_PREFIX}${sessionId}`;
    // Keep only the last 100 messages to avoid storage limits
    const trimmedMessages = messages.slice(-100);
    localStorage.setItem(key, JSON.stringify(trimmedMessages));
  } catch (error) {
    console.error('Failed to save message history:', error);
  }
};

export const getMessageHistory = (sessionId: string): ChatMessage[] => {
  try {
    const key = `${MESSAGE_HISTORY_KEY_PREFIX}${sessionId}`;
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to get message history:', error);
  }
  return [];
};

export const clearMessageHistory = (sessionId: string): void => {
  try {
    const key = `${MESSAGE_HISTORY_KEY_PREFIX}${sessionId}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Failed to clear message history:', error);
  }
};

export const clearAllMessageHistory = (): void => {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(MESSAGE_HISTORY_KEY_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Failed to clear all message history:', error);
  }
};

export const clearAllStorage = (): void => {
  clearStoredSession();
  clearRequestHistory();
  clearUserPreferences();
  clearSearchCache();
  clearAllMessageHistory();
};

// Utility to check available storage space
export const getStorageInfo = (): { used: number; available: number; quota: number } => {
  try {
    let used = 0;
    for (let key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        used += localStorage[key].length;
      }
    }
    
    // Rough estimate of available space (5MB typical limit)
    const quota = 5 * 1024 * 1024; // 5MB in bytes
    const available = quota - used;
    
    return { used, available, quota };
  } catch (error) {
    console.error('Failed to get storage info:', error);
    return { used: 0, available: 0, quota: 0 };
  }
};