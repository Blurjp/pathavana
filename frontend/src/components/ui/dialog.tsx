import React from 'react';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogHeaderProps {
  children: React.ReactNode;
}

interface DialogTitleProps {
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null;

  return (
    <div 
      className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={() => onOpenChange(false)}
    >
      {children}
    </div>
  );
};

export const DialogContent: React.FC<DialogContentProps> = ({ children, className = '' }) => {
  return (
    <div 
      className={`modal-content bg-white rounded-lg p-6 max-w-md w-full mx-4 ${className}`}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  );
};

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children }) => {
  return (
    <div className="modal-header mb-4">
      {children}
    </div>
  );
};

export const DialogTitle: React.FC<DialogTitleProps> = ({ children }) => {
  return (
    <h2 className="modal-title text-xl font-semibold text-gray-900">
      {children}
    </h2>
  );
};