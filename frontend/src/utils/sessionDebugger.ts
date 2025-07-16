/**
 * Session Debugger Utility
 * Helps track session creation and usage issues
 */

interface SessionDebugEvent {
  timestamp: Date;
  event: string;
  data: any;
  stackTrace?: string;
}

class SessionDebugger {
  private events: SessionDebugEvent[] = [];
  private enabled: boolean = true;

  constructor() {
    // Enable debugging if in development mode or debug flag is set
    this.enabled = process.env.NODE_ENV === 'development' || 
                   localStorage.getItem('DEBUG_SESSIONS') === 'true';
    
    if (this.enabled) {
      console.log('🔍 Session Debugger Enabled');
      this.setupInterceptors();
    }
  }

  private setupInterceptors() {
    // Intercept fetch to log API calls
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const [url, options] = args;
      
      // Log session-related API calls
      if (typeof url === 'string' && url.includes('/travel/sessions')) {
        const method = options?.method || 'GET';
        const body = options?.body ? JSON.parse(options.body as string) : null;
        
        this.log('API_CALL', {
          url,
          method,
          body,
          headers: options?.headers
        });

        // Log if creating new session
        if (method === 'POST' && url.endsWith('/sessions')) {
          this.log('🚨 NEW_SESSION_REQUEST', {
            url,
            body,
            stack: this.getStackTrace()
          });
        }
      }

      const response = await originalFetch(...args);
      
      // Log session creation responses
      if (typeof url === 'string' && url.endsWith('/sessions') && response.status === 201) {
        const clonedResponse = response.clone();
        const data = await clonedResponse.json();
        this.log('✅ NEW_SESSION_CREATED', {
          sessionId: data.session_id,
          response: data
        });
      }

      return response;
    };

    // Monitor localStorage
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = (key: string, value: string) => {
      if (key === 'currentSessionId') {
        this.log('LOCALSTORAGE_UPDATE', {
          key,
          oldValue: localStorage.getItem(key),
          newValue: value,
          stack: this.getStackTrace()
        });
      }
      return originalSetItem.call(localStorage, key, value);
    };
  }

  log(event: string, data: any) {
    if (!this.enabled) return;

    const debugEvent: SessionDebugEvent = {
      timestamp: new Date(),
      event,
      data,
      stackTrace: event.includes('NEW_SESSION') ? this.getStackTrace() : undefined
    };

    this.events.push(debugEvent);
    
    // Console log with styling
    const style = event.includes('🚨') ? 'color: red; font-weight: bold;' : 
                  event.includes('✅') ? 'color: green; font-weight: bold;' : 
                  'color: blue;';
    
    console.log(`%c[SessionDebug] ${event}`, style, data);
  }

  private getStackTrace(): string {
    const stack = new Error().stack || '';
    // Remove the first few lines that are from this debugger
    return stack.split('\n').slice(3).join('\n');
  }

  getEvents(): SessionDebugEvent[] {
    return this.events;
  }

  printSummary() {
    console.group('📊 Session Debug Summary');
    console.log(`Total events: ${this.events.length}`);
    
    const sessionCreations = this.events.filter(e => e.event.includes('NEW_SESSION'));
    console.log(`Session creations: ${sessionCreations.length}`);
    
    sessionCreations.forEach((event, index) => {
      console.group(`Session Creation #${index + 1}`);
      console.log('Time:', event.timestamp.toISOString());
      console.log('Data:', event.data);
      if (event.stackTrace) {
        console.log('Stack trace:', event.stackTrace);
      }
      console.groupEnd();
    });
    
    console.groupEnd();
  }

  clear() {
    this.events = [];
    console.log('🧹 Session debug events cleared');
  }

  exportToFile() {
    const dataStr = JSON.stringify(this.events, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `session-debug-${new Date().toISOString()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }
}

// Create singleton instance
export const sessionDebugger = new SessionDebugger();

// Add to window for easy console access
if (typeof window !== 'undefined') {
  (window as any).sessionDebugger = sessionDebugger;
}

// Usage helper
export const debugSession = (event: string, data: any) => {
  sessionDebugger.log(event, data);
};

// React Hook for debugging
export const useSessionDebug = (componentName: string, sessionId?: string) => {
  const debugLog = (event: string, data?: any) => {
    sessionDebugger.log(`[${componentName}] ${event}`, {
      sessionId,
      ...data
    });
  };

  return { debugLog };
};