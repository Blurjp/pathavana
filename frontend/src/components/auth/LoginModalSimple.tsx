import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Mail, Lock, User, AlertCircle, X, Plane } from 'lucide-react';
import { apiClient } from '../../services/api';
import { GoogleLoginButton } from './GoogleLoginButton';
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

  const handleGoogleSuccess = () => {
    onSuccess?.();
    onClose();
    resetForm();
  };

  const handleGoogleError = (errorMessage: string) => {
    setError(errorMessage);
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
            <GoogleLoginButton 
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              setLoading={setIsLoading}
            />
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