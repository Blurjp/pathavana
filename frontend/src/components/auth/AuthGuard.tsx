import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginModal } from './LoginModal';

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
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      setShowLoginModal(true);
      onAuthRequired?.();
    }
  }, [isAuthenticated, isLoading, onAuthRequired]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        {fallback}
        <LoginModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
          onSuccess={() => setShowLoginModal(false)}
        />
      </>
    );
  }

  return <>{children}</>;
};