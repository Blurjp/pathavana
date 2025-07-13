// Date parsing and formatting utilities for travel planning

export const formatDate = (date: string | Date, format: 'short' | 'long' | 'iso' = 'short'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }

  switch (format) {
    case 'short':
      return dateObj.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    case 'long':
      return dateObj.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    case 'iso':
      return dateObj.toISOString().split('T')[0];
    default:
      return dateObj.toLocaleDateString();
  }
};

export const formatTime = (time: string | Date): string => {
  const dateObj = typeof time === 'string' ? new Date(time) : time;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Time';
  }

  return dateObj.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

export const formatDateTime = (dateTime: string | Date): string => {
  const dateObj = typeof dateTime === 'string' ? new Date(dateTime) : dateTime;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid DateTime';
  }

  return `${formatDate(dateObj, 'short')} at ${formatTime(dateObj)}`;
};

export const parseDateInput = (input: string): Date | null => {
  // Handle various date input formats
  const formats = [
    // ISO format
    /^\d{4}-\d{2}-\d{2}$/,
    // US format
    /^\d{1,2}\/\d{1,2}\/\d{4}$/,
    // European format
    /^\d{1,2}\.\d{1,2}\.\d{4}$/,
    // Natural language (basic)
    /^(today|tomorrow|yesterday)$/i
  ];

  const normalizedInput = input.trim().toLowerCase();

  // Handle special cases
  if (normalizedInput === 'today') {
    return new Date();
  }
  if (normalizedInput === 'tomorrow') {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow;
  }
  if (normalizedInput === 'yesterday') {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday;
  }

  // Try parsing as standard date
  const parsed = new Date(input);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }

  return null;
};

export const calculateDuration = (start: string | Date, end: string | Date): string => {
  const startDate = typeof start === 'string' ? new Date(start) : start;
  const endDate = typeof end === 'string' ? new Date(end) : end;

  if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
    return 'Invalid duration';
  }

  const diffMs = endDate.getTime() - startDate.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

  if (diffHours < 1) {
    return `${diffMinutes}m`;
  } else if (diffHours < 24) {
    return diffMinutes > 0 ? `${diffHours}h ${diffMinutes}m` : `${diffHours}h`;
  } else {
    const days = Math.floor(diffHours / 24);
    const remainingHours = diffHours % 24;
    return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
  }
};

export const isValidDateRange = (start: string | Date, end: string | Date): boolean => {
  const startDate = typeof start === 'string' ? new Date(start) : start;
  const endDate = typeof end === 'string' ? new Date(end) : end;

  return !isNaN(startDate.getTime()) && 
         !isNaN(endDate.getTime()) && 
         startDate <= endDate;
};

export const addDays = (date: string | Date, days: number): Date => {
  const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
  dateObj.setDate(dateObj.getDate() + days);
  return dateObj;
};

export const isSameDay = (date1: string | Date, date2: string | Date): boolean => {
  const d1 = typeof date1 === 'string' ? new Date(date1) : date1;
  const d2 = typeof date2 === 'string' ? new Date(date2) : date2;

  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
};

export const getDateRange = (start: string | Date, end: string | Date): Date[] => {
  const startDate = typeof start === 'string' ? new Date(start) : new Date(start);
  const endDate = typeof end === 'string' ? new Date(end) : new Date(end);
  const dates: Date[] = [];

  const currentDate = new Date(startDate);
  while (currentDate <= endDate) {
    dates.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return dates;
};

export const getRelativeTimeString = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMinutes < 1) {
    return 'just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  } else {
    return formatDate(dateObj, 'short');
  }
};