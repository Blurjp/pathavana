import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Mail, Lock, User, AlertCircle, X, Plane } from 'lucide-react';
import { configService } from '../../services/configService';
// import { oauthStateService } from '../../services/oauthStateService'; // No longer needed
import '../../styles/auth.css';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { login, register } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      let success: boolean;
      if (isSignUp) {
        success = await register({ email, password, full_name: fullName });
      } else {
        success = await login({ email, password });
      }

      if (success) {
        onSuccess?.();
        onClose();
        resetForm();
      } else {
        setError(isSignUp ? 'Failed to create account' : 'Invalid email or password');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setFullName('');
    setError('');
  };

  const toggleMode = () => {
    setIsSignUp(!isSignUp);
    setError('');
  };

  const handleSocialLogin = async (provider: 'google' | 'facebook') => {
    setError('');
    setIsLoading(true);
    
    try {
      // Clear cache to force fresh config
      configService.clearCache();
      
      // Get configuration from backend
      const apiBaseUrl = await configService.getApiBaseUrl();
      const redirectUri = await configService.getOAuthRedirectUri();
      
      // Skip the OAuth enabled check for now - we'll check when we get the response
      // const isEnabled = await configService.isOAuthEnabled(provider);
      // if (!isEnabled) {
      //   throw new Error(`${provider.charAt(0).toUpperCase() + provider.slice(1)} OAuth is not configured on the server`);
      // }
      
      const oauthUrl = `${apiBaseUrl}/api/v1/auth/oauth-url/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`;
      
      console.log('OAuth request details:', {
        apiBaseUrl,
        provider,
        redirectUri,
        fullUrl: oauthUrl
      });
      
      const response = await fetch(oauthUrl);
      
      if (!response.ok) {
        let errorMessage = 'Failed to get OAuth URL';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // If response is not JSON, use status text
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      // Check if OAuth is configured
      if (!data.auth_url) {
        throw new Error(`${provider.charAt(0).toUpperCase() + provider.slice(1)} OAuth is not configured on the server`);
      }
      
      // Store the state in localStorage
      localStorage.setItem('oauth_state', data.state);
      localStorage.setItem('oauth_provider', provider);
      
      // Redirect to OAuth provider
      window.location.href = data.auth_url;
      
    } catch (err: any) {
      console.error('OAuth error:', err);
      
      // Check if it's a network error
      if (err.message === 'Failed to fetch') {
        setError('Cannot connect to server. Please ensure the backend is running on port 8001.');
      } else {
        setError(err.message || `Failed to connect with ${provider.charAt(0).toUpperCase() + provider.slice(1)}`);
      }
      
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="auth-modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div 
        className="auth-modal-content animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="auth-close-btn"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <Plane className="h-7 w-7" />
          </div>
          <h2 className="auth-title">
            {isSignUp ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="auth-subtitle">
            {isSignUp 
              ? 'Start planning amazing trips with AI assistance' 
              : 'Sign in to continue your travel planning journey'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {/* Error Message */}
          {error && (
            <div className="auth-error">
              <AlertCircle className="auth-error-icon h-5 w-5" />
              <span className="auth-error-text">{error}</span>
            </div>
          )}

          {/* Full Name Field (Sign Up only) */}
          {isSignUp && (
            <div className="auth-field">
              <label htmlFor="fullName" className="auth-label">
                Full Name
              </label>
              <div className="auth-input-wrapper">
                <input
                  id="fullName"
                  type="text"
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="auth-input"
                  required={isSignUp}
                />
                <User className="auth-input-icon h-5 w-5" />
              </div>
            </div>
          )}

          {/* Email Field */}
          <div className="auth-field">
            <label htmlFor="email" className="auth-label">
              Email Address
            </label>
            <div className="auth-input-wrapper">
              <input
                id="email"
                type="email"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                required
              />
              <Mail className="auth-input-icon h-5 w-5" />
            </div>
          </div>

          {/* Password Field */}
          <div className="auth-field">
            <label htmlFor="password" className="auth-label">
              Password
            </label>
            <div className="auth-input-wrapper">
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                required
                minLength={8}
              />
              <Lock className="auth-input-icon h-5 w-5" />
            </div>
            {isSignUp && (
              <p className="auth-password-hint">
                <span>Must be at least 8 characters with uppercase and number</span>
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="auth-spinner" />
                <span>Please wait...</span>
              </>
            ) : (
              <span>{isSignUp ? 'Create Account' : 'Sign In'}</span>
            )}
          </button>

          {/* Divider */}
          <div className="auth-divider">
            <span className="auth-divider-text">or continue with</span>
          </div>

          {/* Social Login Buttons */}
          <div className="auth-social-buttons">
            <button 
              type="button" 
              className="auth-social-btn" 
              onClick={() => handleSocialLogin('google')}
              disabled={isLoading}
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span>Google</span>
            </button>
            <button 
              type="button" 
              className="auth-social-btn" 
              onClick={() => handleSocialLogin('facebook')}
              disabled={isLoading}
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
              <span>Facebook</span>
            </button>
          </div>

          {/* Toggle */}
          <div className="auth-toggle">
            <span className="auth-toggle-text">
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}
            </span>
            <button
              type="button"
              onClick={toggleMode}
              className="auth-toggle-btn"
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};