import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useAuth } from '../../contexts/AuthContext';
import { Mail, Lock, User, AlertCircle } from 'lucide-react';

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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isSignUp ? 'Create Account' : 'Sign In'}</DialogTitle>
          <DialogDescription>
            {isSignUp 
              ? 'Create your account to start planning your trips' 
              : 'Sign in to access your trips and travel sessions'}
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {isSignUp && (
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="fullName"
                  type="text"
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
                  className="pl-10"
                  required={isSignUp}
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                className="pl-10"
                required
                minLength={8}
              />
            </div>
            {isSignUp && (
              <p className="text-xs text-gray-500">
                Password must be at least 8 characters with uppercase and number
              </p>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-md text-sm">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          <div className="flex flex-col gap-3">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Loading...' : (isSignUp ? 'Create Account' : 'Sign In')}
            </Button>
            
            <div className="text-center text-sm">
              <span className="text-gray-600">
                {isSignUp ? 'Already have an account?' : "Don't have an account?"}
              </span>{' '}
              <button
                type="button"
                onClick={toggleMode}
                className="text-primary hover:underline font-medium"
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};