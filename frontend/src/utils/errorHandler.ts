// Error handling utilities for the application

export interface AppError {
  message: string;
  code?: string;
  context?: any;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export class ErrorHandler {
  private static errors: AppError[] = [];
  private static maxErrors = 100;

  static logError(error: Error | string, context?: any, severity: AppError['severity'] = 'medium'): void {
    const appError: AppError = {
      message: typeof error === 'string' ? error : error.message,
      code: typeof error === 'object' && 'code' in error ? (error as any).code : undefined,
      context,
      timestamp: new Date().toISOString(),
      severity
    };

    this.errors.push(appError);
    
    // Keep only recent errors
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(-this.maxErrors);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('App Error:', appError);
    }

    // Send to error reporting service in production
    if (process.env.NODE_ENV === 'production' && severity === 'critical') {
      this.reportError(appError);
    }
  }

  static getErrors(): AppError[] {
    return [...this.errors];
  }

  static clearErrors(): void {
    this.errors = [];
  }

  static getErrorsBySeveity(severity: AppError['severity']): AppError[] {
    return this.errors.filter(error => error.severity === severity);
  }

  private static async reportError(error: AppError): Promise<void> {
    try {
      // In a real application, you would send this to your error reporting service
      // For example: Sentry, LogRocket, Bugsnag, etc.
      console.error('Critical error reported:', error);
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }
}

// Specific error handlers for common scenarios
export const handleApiError = (error: any, context?: string): string => {
  let message = 'An unexpected error occurred';

  if (error?.response) {
    // HTTP error response
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        message = data?.message || 'Invalid request. Please check your input.';
        break;
      case 401:
        message = 'Authentication required. Please log in.';
        break;
      case 403:
        message = 'Access denied. You don\'t have permission for this action.';
        break;
      case 404:
        message = 'The requested resource was not found.';
        break;
      case 429:
        message = 'Too many requests. Please try again later.';
        break;
      case 500:
        message = 'Server error. Please try again later.';
        break;
      case 503:
        message = 'Service temporarily unavailable. Please try again later.';
        break;
      default:
        message = data?.message || `Request failed with status ${status}`;
    }

    ErrorHandler.logError(message, { 
      status, 
      url: error.config?.url,
      method: error.config?.method,
      context 
    }, status >= 500 ? 'high' : 'medium');
  } else if (error?.request) {
    // Network error
    message = 'Network error. Please check your connection and try again.';
    ErrorHandler.logError(message, { context }, 'high');
  } else {
    // Other error
    message = error?.message || message;
    ErrorHandler.logError(message, { context }, 'medium');
  }

  return message;
};

export const handleValidationError = (errors: any): string[] => {
  if (Array.isArray(errors)) {
    return errors.map(error => error.message || String(error));
  }

  if (typeof errors === 'object' && errors !== null) {
    return Object.values(errors).flat().map(error => String(error));
  }

  return [String(errors)];
};

export const handleFileUploadError = (error: any): string => {
  if (error?.code === 'FILE_TOO_LARGE') {
    return 'File is too large. Please select a smaller file.';
  }

  if (error?.code === 'INVALID_FILE_TYPE') {
    return 'Invalid file type. Please select a supported file format.';
  }

  if (error?.code === 'UPLOAD_FAILED') {
    return 'Upload failed. Please try again.';
  }

  return handleApiError(error, 'file_upload');
};

export const handleSessionError = (error: any): string => {
  if (error?.code === 'SESSION_EXPIRED') {
    return 'Your session has expired. Please log in again.';
  }

  if (error?.code === 'SESSION_NOT_FOUND') {
    return 'Session not found. Starting a new session.';
  }

  if (error?.code === 'SESSION_INVALID') {
    return 'Invalid session. Please start a new session.';
  }

  return handleApiError(error, 'session');
};

export const handleSearchError = (error: any): string => {
  if (error?.code === 'NO_RESULTS') {
    return 'No results found for your search. Try different criteria.';
  }

  if (error?.code === 'SEARCH_TIMEOUT') {
    return 'Search timed out. Please try again with more specific criteria.';
  }

  if (error?.code === 'RATE_LIMITED') {
    return 'Too many searches. Please wait a moment before searching again.';
  }

  return handleApiError(error, 'search');
};

// Global error boundary helper
export const createErrorBoundaryHandler = (componentName: string) => {
  return (error: Error, errorInfo: any) => {
    ErrorHandler.logError(error, {
      component: componentName,
      errorInfo
    }, 'high');
  };
};

// Promise rejection handler
export const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
  ErrorHandler.logError(
    event.reason || 'Unhandled promise rejection',
    { type: 'unhandled_rejection' },
    'high'
  );
};

// Global error handler
export const handleGlobalError = (event: ErrorEvent) => {
  ErrorHandler.logError(
    event.error || event.message,
    {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      type: 'global_error'
    },
    'high'
  );
};

// Retry helper
export const withRetry = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: any;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }

      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt - 1)));
    }
  }

  throw lastError;
};