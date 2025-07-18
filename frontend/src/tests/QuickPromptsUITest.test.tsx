import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UnifiedTravelRequest from '../pages/UnifiedTravelRequest';
import { AuthProvider } from '../contexts/AuthContext';
import { SidebarProvider } from '../contexts/SidebarContext';
import * as api from '../services/api';

// Mock the API module
jest.mock('../services/api');

// Create mock data outside
const mockMessages: any[] = [];
const mockSendMessage = jest.fn();

// Mock useChatManager hook
jest.mock('../hooks/useChatManager', () => ({
  useChatManager: () => {
    return {
      messages: mockMessages,
      sendMessage: mockSendMessage,
      isLoading: false,
      error: null,
      searchResults: null,
      isSearching: false,
      clearError: jest.fn(),
      clearMessages: jest.fn(),
      retryLastMessage: jest.fn(),
    };
  }
}));

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <SidebarProvider>
          <UnifiedTravelRequest />
        </SidebarProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Quick Prompts UI Test', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset mock data
    mockMessages.length = 0;
    mockSendMessage.mockClear();
    
    // Setup mock to add messages
    mockSendMessage.mockImplementation(async (message: string) => {
      // Add user message
      mockMessages.push({
        id: '1',
        type: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      });
      
      // Add AI response with suggestions
      mockMessages.push({
        id: '2',
        type: 'assistant',
        content: 'I\'d be happy to help you plan your trip to Tokyo! To get started, I need some more information.',
        timestamp: new Date().toISOString(),
        metadata: {
          suggestions: [
            'I want to go next month',
            'I\'m flexible with dates',
            'Show me flights for specific dates'
          ],
          clarifying_questions: [
            'When would you like to travel to Tokyo?',
            'How many days are you planning to stay?',
            'What\'s your budget for this trip?'
          ],
          orchestrator_suggestions: [
            'Search for flights to Tokyo in March',
            'Find hotels in Shibuya area',
            'Show me popular activities in Tokyo'
          ],
          hints: [
            { text: 'Tokyo is beautiful in cherry blossom season (late March to early April)' },
            { text: 'Consider getting a JR Pass for transportation' },
            { text: 'Book hotels early for better rates' }
          ]
        }
      });
    });
  });

  it('should display initial static quick prompts', () => {
    renderComponent();
    
    // Check for initial quick prompts
    const quickPrompts = screen.getAllByRole('button', { name: /quick prompt/i });
    expect(quickPrompts.length).toBeGreaterThan(0);
    
    // Check for specific initial prompts
    expect(screen.getByText('I want to plan a trip to Paris')).toBeInTheDocument();
    expect(screen.getByText('Find me flights to Tokyo next month')).toBeInTheDocument();
  });

  it('should update quick prompts based on AI response metadata', async () => {
    renderComponent();
    
    // Get initial quick prompts
    const initialPrompts = screen.getAllByRole('button', { name: /quick prompt/i });
    const initialPromptTexts = initialPrompts.map(p => p.textContent);
    
    // Send a message
    const chatInput = screen.getByPlaceholderText(/where would you like to travel/i);
    fireEvent.change(chatInput, { target: { value: 'I want to plan a trip to Tokyo' } });
    fireEvent.keyDown(chatInput, { key: 'Enter', code: 'Enter' });
    
    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText(/I'd be happy to help you plan your trip to Tokyo/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Check if quick prompts have updated
    await waitFor(() => {
      const updatedPrompts = screen.getAllByRole('button', { name: /quick prompt/i });
      const updatedPromptTexts = updatedPrompts.map(p => p.textContent);
      
      // Should have different prompts now
      expect(updatedPromptTexts).not.toEqual(initialPromptTexts);
      
      // Should include AI-suggested prompts
      expect(updatedPromptTexts.some(text => 
        text?.includes('When would you like to travel') ||
        text?.includes('Search for flights to Tokyo') ||
        text?.includes('I want to go next month')
      )).toBe(true);
    });
  });

  it('should prioritize different types of suggestions correctly', async () => {
    renderComponent();
    
    // Send a message to trigger AI response
    const chatInput = screen.getByPlaceholderText(/where would you like to travel/i);
    fireEvent.change(chatInput, { target: { value: 'Tokyo trip' } });
    fireEvent.keyDown(chatInput, { key: 'Enter', code: 'Enter' });
    
    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText(/I'd be happy to help/i)).toBeInTheDocument();
    });
    
    // Get the quick prompts after AI response
    const quickPrompts = screen.getAllByRole('button', { name: /quick prompt/i });
    const promptTexts = quickPrompts.map(p => p.textContent);
    
    // Should prioritize orchestrator_suggestions first
    expect(promptTexts[0]).toContain('Search for flights to Tokyo');
    
    // Should show a mix of different suggestion types
    const hasOrchestratorSuggestion = promptTexts.some(text => text?.includes('Search for flights'));
    const hasClarifyingQuestion = promptTexts.some(text => text?.includes('When would you like'));
    const hasRegularSuggestion = promptTexts.some(text => text?.includes('I want to go next month'));
    
    expect(hasOrchestratorSuggestion || hasClarifyingQuestion || hasRegularSuggestion).toBe(true);
  });

  it('should limit quick prompts to 5 items', async () => {
    renderComponent();
    
    // Send a message
    const chatInput = screen.getByPlaceholderText(/where would you like to travel/i);
    fireEvent.change(chatInput, { target: { value: 'Plan a trip' } });
    fireEvent.keyDown(chatInput, { key: 'Enter', code: 'Enter' });
    
    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText(/I'd be happy to help/i)).toBeInTheDocument();
    });
    
    // Check that we have at most 5 quick prompts
    const quickPrompts = screen.getAllByRole('button', { name: /quick prompt/i });
    expect(quickPrompts.length).toBeLessThanOrEqual(5);
  });

  it('should send message when quick prompt is clicked', async () => {
    const mockSendMessage = jest.fn();
    
    // Override the mock to capture sendMessage calls
    jest.mocked(require('../hooks/useChatManager').useChatManager).mockReturnValue({
      messages: [],
      sendMessage: mockSendMessage,
      isLoading: false,
      error: null,
      searchResults: null,
      isSearching: false,
      clearError: jest.fn(),
      clearMessages: jest.fn(),
      retryLastMessage: jest.fn(),
    });
    
    renderComponent();
    
    // Click a quick prompt
    const quickPrompt = screen.getByText('I want to plan a trip to Paris');
    fireEvent.click(quickPrompt);
    
    // Verify sendMessage was called
    expect(mockSendMessage).toHaveBeenCalledWith('I want to plan a trip to Paris');
  });
});