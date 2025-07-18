/**
 * Mock data service for testing when backend search is unavailable
 */

import { SearchResults } from '../types';
import apiClient from './api';

class MockDataService {
  private baseUrl = '/api/v1/mock';

  async getChatWithMockResults(message: string): Promise<any> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/chat-with-results`, {
        message
      });
      
      if (response.success && response.data) {
        return response.data;
      }
      
      return null;
    } catch (error) {
      console.error('Error fetching mock data:', error);
      return null;
    }
  }

  async getMockSearchResults(searchType: 'flights' | 'hotels' | 'all'): Promise<SearchResults | null> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/test-search/${searchType}`);
      
      if (response.success && response.data) {
        const data = response.data as any;
        if (data.searchResults) {
          return data.searchResults;
        }
      }
      
      return null;
    } catch (error) {
      console.error('Error fetching mock search results:', error);
      return null;
    }
  }

  // Check if we should use mock data based on the response
  shouldUseMockData(assistantMessage: string): boolean {
    const noResultsIndicators = [
      'unable to retrieve',
      'unable to access',
      'technical issue',
      'technical error',
      'couldn\'t retrieve',
      'could not retrieve',
      'no results found',
      'try again'
    ];
    
    const lowerMessage = assistantMessage.toLowerCase();
    return noResultsIndicators.some(indicator => lowerMessage.includes(indicator));
  }
}

export default new MockDataService();