import { apiClient } from './api';
import { TravelContext, ApiResponse } from '../types';

export class ContextAPI {
  // Context CRUD operations
  async getContext(sessionId: string): Promise<ApiResponse<TravelContext>> {
    return apiClient.get(`/api/v1/context/${sessionId}`);
  }

  async createContext(
    sessionId: string, 
    context: TravelContext
  ): Promise<ApiResponse<TravelContext>> {
    return apiClient.post(`/api/v1/context/${sessionId}`, context);
  }

  async updateContext(
    sessionId: string, 
    updates: Partial<TravelContext>
  ): Promise<ApiResponse<TravelContext>> {
    return apiClient.put(`/api/v1/context/${sessionId}`, updates);
  }

  async deleteContext(sessionId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/api/v1/context/${sessionId}`);
  }

  // Context operations
  async addToSearchHistory(
    sessionId: string, 
    request: any
  ): Promise<ApiResponse<TravelContext>> {
    return apiClient.post(`/api/v1/context/${sessionId}/search-history`, request);
  }

  async updateSelectedOptions(
    sessionId: string, 
    options: any
  ): Promise<ApiResponse<TravelContext>> {
    return apiClient.put(`/api/v1/context/${sessionId}/selections`, options);
  }

  async clearContext(sessionId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/api/v1/context/${sessionId}/clear`);
  }

  // Smart context inference
  async inferContextFromMessage(
    message: string, 
    currentContext?: TravelContext
  ): Promise<ApiResponse<Partial<TravelContext>>> {
    return apiClient.post('/api/v1/context/infer', {
      message,
      currentContext
    });
  }

  async getContextSuggestions(
    sessionId: string
  ): Promise<ApiResponse<string[]>> {
    return apiClient.get(`/api/v1/context/${sessionId}/suggestions`);
  }
}

export const contextAPI = new ContextAPI();