import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

export const Input: React.FC<InputProps> = ({ className = '', ...props }) => {
  const baseClasses = 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm';
  
  return (
    <input
      className={`${baseClasses} ${className}`}
      {...props}
    />
  );
};