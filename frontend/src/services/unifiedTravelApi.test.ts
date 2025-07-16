import { UnifiedTravelApi } from './unifiedTravelApi';
import { apiClient } from './api';

// Mock the API client
jest.mock('./api');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('UnifiedTravelApi', () => {
  let travelApi: UnifiedTravelApi;

  beforeEach(() => {
    travelApi = new UnifiedTravelApi();
    jest.clearAllMocks();
  });

  describe('API URL Configuration', () => {
    it('should use the correct API version in the base URL', () => {
      // Check that the baseUrl includes v1
      expect((travelApi as any).baseUrl).toBe('/api/v1/travel');
    });

    it('should call getSession with the correct URL', async () => {
      const sessionId = 'test-session-123';
      mockedApiClient.get.mockResolvedValue({
        success: true,
        data: { id: sessionId }
      });

      await travelApi.getSession(sessionId);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/api/v1/travel/sessions/${sessionId}`
      );
    });

    it('should call createSession with the correct URL', async () => {
      mockedApiClient.post.mockResolvedValue({
        success: true,
        data: { sessionId: 'new-session-123' }
      });

      await travelApi.createSession('Hello');

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/travel/sessions',
        expect.objectContaining({
          message: 'Hello',
          source: 'web'
        })
      );
    });

    it('should call sendChatMessage with the correct URL', async () => {
      const sessionId = 'test-session-123';
      mockedApiClient.post.mockResolvedValue({
        success: true,
        data: { response: 'AI response' }
      });

      await travelApi.sendChatMessage('Find flights', sessionId);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        `/api/v1/travel/sessions/${sessionId}/chat`,
        expect.objectContaining({
          message: 'Find flights'
        })
      );
    });
  });
});