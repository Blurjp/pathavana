// Configuration service to fetch backend config dynamically

interface FrontendConfig {
  apiBaseUrl: string;
  oauthRedirectUri: string;
  corsOrigins: string[];
  features: {
    googleOAuth: boolean;
    facebookOAuth: boolean;
  };
}

class ConfigService {
  private config: FrontendConfig | null = null;
  private configPromise: Promise<FrontendConfig> | null = null;
  private lastFetch: number = 0;
  private configCheckInterval: number = 10000; // Check every 10 seconds
  private intervalId: NodeJS.Timeout | null = null;

  constructor() {
    // Start periodic config checks
    this.startConfigWatcher();
  }

  private startConfigWatcher() {
    // Check config periodically for changes
    this.intervalId = setInterval(async () => {
      if (this.config) {
        try {
          const newConfig = await this.fetchConfig();
          // Check if OAuth status changed
          if (newConfig.features.googleOAuth !== this.config.features.googleOAuth ||
              newConfig.features.facebookOAuth !== this.config.features.facebookOAuth) {
            console.log('OAuth configuration changed:', newConfig.features);
            this.config = newConfig;
            // Dispatch custom event so components can react
            window.dispatchEvent(new CustomEvent('oauth-config-changed', { detail: newConfig }));
          }
        } catch (error) {
          console.warn('Failed to check config update:', error);
        }
      }
    }, this.configCheckInterval);
  }

  async getConfig(): Promise<FrontendConfig> {
    const now = Date.now();
    
    // Return cached config if it's fresh (less than 5 seconds old)
    if (this.config && (now - this.lastFetch) < 5000) {
      return this.config;
    }

    // Return existing promise if already fetching
    if (this.configPromise) {
      return this.configPromise;
    }

    // Fetch config from backend
    this.configPromise = this.fetchConfig();
    this.config = await this.configPromise;
    this.lastFetch = now;
    this.configPromise = null;

    return this.config;
  }

  private async fetchConfig(): Promise<FrontendConfig> {
    try {
      // Try to fetch from backend first
      const backendUrl = this.getBackendUrl();
      const response = await fetch(`${backendUrl}/api/v1/frontend-config`);
      
      if (response.ok) {
        const config = await response.json();
        console.log('Loaded config from backend:', config);
        return config;
      }
    } catch (error) {
      console.warn('Failed to fetch config from backend, using defaults:', error);
    }

    // Fallback to default configuration
    const defaultConfig: FrontendConfig = {
      apiBaseUrl: this.getBackendUrl(),
      oauthRedirectUri: `${window.location.origin}/auth/callback`,
      corsOrigins: ['http://localhost:3000'],
      features: {
        googleOAuth: false,
        facebookOAuth: false
      }
    };

    console.log('Using default config:', defaultConfig);
    return defaultConfig;
  }

  private getBackendUrl(): string {
    // Always use port 8001 for development
    return 'http://localhost:8001';
  }

  // Get specific config values
  async getApiBaseUrl(): Promise<string> {
    const config = await this.getConfig();
    return config.apiBaseUrl;
  }

  async getOAuthRedirectUri(): Promise<string> {
    const config = await this.getConfig();
    return config.oauthRedirectUri;
  }

  async isOAuthEnabled(provider: 'google' | 'facebook'): Promise<boolean> {
    const config = await this.getConfig();
    return provider === 'google' ? config.features.googleOAuth : config.features.facebookOAuth;
  }

  // Clear cached config (for testing or when backend restarts)
  clearCache(): void {
    this.config = null;
    this.configPromise = null;
    this.lastFetch = 0;
  }

  // Stop config watcher (for cleanup)
  stopConfigWatcher(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}

export const configService = new ConfigService();