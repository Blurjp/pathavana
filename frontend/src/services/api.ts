import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ApiResponse } from '../types';
import { configService } from './configService';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8001', // Default, will be updated dynamically
      timeout: 0, // No timeout - let the request complete
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.updateBaseURL(); // Update base URL from config
  }

  private async updateBaseURL() {
    try {
      const baseURL = await configService.getApiBaseUrl();
      this.client.defaults.baseURL = baseURL;
    } catch (error) {
      console.warn('Failed to update API base URL from config:', error);
    }
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          // Don't redirect, let the AuthGuard handle showing login modal
          // This prevents infinite redirect loops
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, params?: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get(url, { params });
      // If the backend response has our standard structure, unwrap it
      if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
        return {
          success: response.data.success,
          data: response.data.data,
          error: response.data.error,
          metadata: response.data.metadata,
        };
      }
      // Otherwise return as is
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'An error occurred',
      };
    }
  }

  async post<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post(url, data, config);
      // If the backend response has our standard structure, unwrap it
      if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
        return {
          success: response.data.success,
          data: response.data.data,
          error: response.data.error,
          metadata: response.data.metadata,
        };
      }
      // Otherwise return as is
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred',
      };
    }
  }

  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put(url, data);
      // If the backend response has our standard structure, unwrap it
      if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
        return {
          success: response.data.success,
          data: response.data.data,
          error: response.data.error,
          metadata: response.data.metadata,
        };
      }
      // Otherwise return as is
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'An error occurred',
      };
    }
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.delete(url);
      // If the backend response has our standard structure, unwrap it
      if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
        return {
          success: response.data.success,
          data: response.data.data,
          error: response.data.error,
          metadata: response.data.metadata,
        };
      }
      // Otherwise return as is
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'An error occurred',
      };
    }
  }

  // Specific method for file uploads
  async upload<T>(url: string, formData: FormData): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Upload failed',
      };
    }
  }

  // Get the current base URL
  getBaseURL(): string {
    return this.client.defaults.baseURL || 'http://localhost:8001';
  }
}

export const apiClient = new ApiClient();
export default apiClient;