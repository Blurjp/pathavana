import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onAuthRequired?: () => void;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  fallback = null,
  onAuthRequired 
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      onAuthRequired?.();
      // Redirect to homepage
      navigate('/');
    }
  }, [isAuthenticated, isLoading, onAuthRequired, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Return null or fallback while redirecting
    return <>{fallback}</>;
  }

  return <>{children}</>;
};