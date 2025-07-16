import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthState, LoginCredentials, RegisterData } from '../types';
import { apiClient } from '../services/api';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => void;
  updateUser: (updates: Partial<User>) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    isLoading: true,
  });

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return;
      }

      const response = await apiClient.get<User>('/api/v1/auth/me');
      if (response.success && response.data) {
        setAuthState({
          isAuthenticated: true,
          user: response.data,
          token,
          isLoading: false,
        });
      } else {
        localStorage.removeItem('auth_token');
        setAuthState({
          isAuthenticated: false,
          user: null,
          token: null,
          isLoading: false,
        });
      }
    } catch (error) {
      localStorage.removeItem('auth_token');
      setAuthState({
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
      });
    }
  };

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      
      // Send as JSON with email and password
      const response = await apiClient.post<{ access_token: string; refresh_token: string; user: User }>('/api/v1/auth/login', {
        email: credentials.email,
        password: credentials.password
      });
      
      if (response.success && response.data) {
        const { user, access_token } = response.data;
        localStorage.setItem('auth_token', access_token);
        setAuthState({
          isAuthenticated: true,
          user,
          token: access_token,
          isLoading: false,
        });
        return true;
      } else {
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return false;
      }
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      return false;
    }
  };

  const register = async (data: RegisterData): Promise<boolean> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      
      const response = await apiClient.post<{ access_token: string; refresh_token: string; user: User }>('/api/v1/auth/register', data);
      
      if (response.success && response.data) {
        const { user, access_token } = response.data;
        localStorage.setItem('auth_token', access_token);
        setAuthState({
          isAuthenticated: true,
          user,
          token: access_token,
          isLoading: false,
        });
        return true;
      } else {
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return false;
      }
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setAuthState({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
    });
  };

  const updateUser = async (updates: Partial<User>): Promise<boolean> => {
    try {
      const response = await apiClient.put<User>('/api/v1/auth/profile', updates);
      
      if (response.success && response.data) {
        setAuthState(prev => ({
          ...prev,
          user: response.data || null,
        }));
        return true;
      }
      return false;
    } catch (error) {
      return false;
    }
  };

  const value: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};