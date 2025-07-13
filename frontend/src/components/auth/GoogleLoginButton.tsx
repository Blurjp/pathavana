import React from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { apiClient } from '../../services/api';

interface GoogleLoginButtonProps {
  onSuccess: () => void;
  onError: (error: string) => void;
  setLoading: (loading: boolean) => void;
}

export const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({ 
  onSuccess, 
  onError, 
  setLoading 
}) => {
  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      onError('No credential received from Google');
      return;
    }

    setLoading(true);
    
    try {
      // Send the ID token to our backend
      const response = await apiClient.post<{
        access_token: string;
        refresh_token?: string;
        token_type: string;
        expires_in: number;
        user?: any;
      }>('/api/v1/auth/google-login', {
        id_token: credentialResponse.credential
      });
      
      if (response.success && response.data) {
        // Store tokens
        localStorage.setItem('auth_token', response.data.access_token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        
        // Update auth context
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        
        onSuccess();
        
        // Force a page reload to update auth state
        window.location.reload();
      } else {
        throw new Error(response.error || 'Google login failed');
      }
    } catch (err: any) {
      console.error('Google login error:', err);
      onError(err.message || 'Failed to connect with Google');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    onError('Google login failed');
  };

  return (
    <div className="w-full">
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        useOneTap={false}
        theme="outline"
        size="large"
        width="100%"
        text="continue_with"
        shape="rectangular"
      />
    </div>
  );
};