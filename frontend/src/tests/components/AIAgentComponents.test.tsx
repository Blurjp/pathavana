/**
 * UI Component interaction tests for AI Travel Agent components
 * Tests user interactions, rendering, and component behavior
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CardMessage } from '../../components/ChatMessage/CardMessage';
import { QuickActions } from '../../components/ChatMessage/QuickActions';
import { EnhancedChatMessage } from '../../components/ChatMessage/EnhancedChatMessage';
import { 
  CardResponse, 
  ConversationState, 
  EnhancedChatMessage as ChatMessageType 
} from '../../types/AIAgentTypes';

describe('AI Travel Agent UI Components', () => {
  describe('CardMessage Component', () => {
    const mockCardResponse: CardResponse = {
      type: 'card',
      cards: [
        {
          title: 'ANA Flight NH101',
          subtitle: 'JFK → NRT',
          image: 'https://example.com/airline-logo.jpg',
          details: {
            'Departure': 'Mar 15, 10:00 AM',
            'Arrival': 'Mar 16, 2:30 PM',
            'Duration': '14h 30m',
            'Price': '$850',
            'Stops': 'Non-stop'
          },
          actions: [
            {
              label: 'Add to Plan',
              action: 'add_to_plan',
              data: { type: 'flight', id: 'flight-1' }
            },
            {
              label: 'View Details',
              action: 'view_details',
              data: { type: 'flight', id: 'flight-1' }
            }
          ]
        },
        {
          title: 'Tokyo Grand Hotel',
          subtitle: 'Shibuya - 4★',
          details: {
            'Price': '$200/night',
            'Location': '123 Shibuya Street',
            'Rating': '8.5/10 (1200 reviews)',
            'Amenities': 'WiFi, Pool, Gym'
          },
          actions: [
            {
              label: 'Add to Plan',
              action: 'add_to_plan',
              data: { type: 'hotel', id: 'hotel-1' }
            },
            {
              label: 'Book Now',
              action: 'book_now',
              data: { type: 'hotel', id: 'hotel-1' }
            }
          ]
        }
      ]
    };

    it('should render card information correctly', () => {
      const mockOnAction = jest.fn();
      render(<CardMessage response={mockCardResponse} onAction={mockOnAction} />);

      // Check flight card
      expect(screen.getByText('ANA Flight NH101')).toBeInTheDocument();
      expect(screen.getByText('JFK → NRT')).toBeInTheDocument();
      expect(screen.getByText('Mar 15, 10:00 AM')).toBeInTheDocument();
      expect(screen.getByText('$850')).toBeInTheDocument();
      expect(screen.getByText('Non-stop')).toBeInTheDocument();

      // Check hotel card
      expect(screen.getByText('Tokyo Grand Hotel')).toBeInTheDocument();
      expect(screen.getByText('Shibuya - 4★')).toBeInTheDocument();
      expect(screen.getByText('$200/night')).toBeInTheDocument();
      expect(screen.getByText('8.5/10 (1200 reviews)')).toBeInTheDocument();
    });

    it('should render action buttons correctly', () => {
      const mockOnAction = jest.fn();
      render(<CardMessage response={mockCardResponse} onAction={mockOnAction} />);

      // Check flight actions
      const addToPlans = screen.getAllByText('Add to Plan');
      expect(addToPlans).toHaveLength(2);

      // Check hotel-specific actions
      expect(screen.getByText('Book Now')).toBeInTheDocument();
      expect(screen.getByText('View Details')).toBeInTheDocument();
    });

    it('should handle action button clicks', async () => {
      const user = userEvent.setup();
      const mockOnAction = jest.fn();
      render(<CardMessage response={mockCardResponse} onAction={mockOnAction} />);

      // Click "Add to Plan" for flight
      const addToPlans = screen.getAllByText('Add to Plan');
      await user.click(addToPlans[0]);

      expect(mockOnAction).toHaveBeenCalledWith('add_to_plan', {
        type: 'flight',
        id: 'flight-1'
      });

      // Click "Book Now" for hotel
      const bookNowButton = screen.getByText('Book Now');
      await user.click(bookNowButton);

      expect(mockOnAction).toHaveBeenCalledWith('book_now', {
        type: 'hotel',
        id: 'hotel-1'
      });
    });

    it('should render images when provided', () => {
      const mockOnAction = jest.fn();
      render(<CardMessage response={mockCardResponse} onAction={mockOnAction} />);

      const image = screen.getByAltText('ANA Flight NH101');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/airline-logo.jpg');
    });

    it('should handle missing images gracefully', () => {
      const responseWithoutImage: CardResponse = {
        type: 'card',
        cards: [{
          title: 'Test Card',
          subtitle: 'Test Subtitle',
          details: { 'Price': '$100' },
          actions: []
        }]
      };

      const mockOnAction = jest.fn();
      render(<CardMessage response={responseWithoutImage} onAction={mockOnAction} />);

      expect(screen.getByText('Test Card')).toBeInTheDocument();
      // Should not crash without image
    });

    it('should apply correct CSS classes for different action types', () => {
      const mockOnAction = jest.fn();
      render(<CardMessage response={mockCardResponse} onAction={mockOnAction} />);

      const addToPlanButtons = screen.getAllByText('Add to Plan');
      expect(addToPlanButtons[0]).toHaveClass('add_to_plan');

      const bookNowButton = screen.getByText('Book Now');
      expect(bookNowButton).toHaveClass('book_now');

      const viewDetailsButton = screen.getByText('View Details');
      expect(viewDetailsButton).toHaveClass('view_details');
    });
  });

  describe('QuickActions Component', () => {
    it('should render greeting state actions', () => {
      const mockOnActionClick = jest.fn();
      render(
        <QuickActions 
          conversationState={ConversationState.GREETING} 
          onActionClick={mockOnActionClick} 
        />
      );

      expect(screen.getByText('Plan a trip')).toBeInTheDocument();
      expect(screen.getByText('View my plans')).toBeInTheDocument();
      expect(screen.getByText('Check bookings')).toBeInTheDocument();

      // Check for emojis
      expect(screen.getByText('✈️')).toBeInTheDocument();
      expect(screen.getByText('📋')).toBeInTheDocument();
      expect(screen.getByText('🎫')).toBeInTheDocument();
    });

    it('should render searching state actions', () => {
      const mockOnActionClick = jest.fn();
      render(
        <QuickActions 
          conversationState={ConversationState.SEARCHING} 
          onActionClick={mockOnActionClick} 
        />
      );

      expect(screen.getByText('Change dates')).toBeInTheDocument();
      expect(screen.getByText('Filter results')).toBeInTheDocument();
      expect(screen.getByText('Compare options')).toBeInTheDocument();
    });

    it('should render booking state actions', () => {
      const mockOnActionClick = jest.fn();
      render(
        <QuickActions 
          conversationState={ConversationState.BOOKING} 
          onActionClick={mockOnActionClick} 
        />
      );

      expect(screen.getByText('Payment info')).toBeInTheDocument();
      expect(screen.getByText('Traveler details')).toBeInTheDocument();
      expect(screen.getByText('Review booking')).toBeInTheDocument();
    });

    it('should handle action clicks correctly', async () => {
      const user = userEvent.setup();
      const mockOnActionClick = jest.fn();
      render(
        <QuickActions 
          conversationState={ConversationState.GREETING} 
          onActionClick={mockOnActionClick} 
        />
      );

      const planTripButton = screen.getByText('Plan a trip');
      await user.click(planTripButton);

      expect(mockOnActionClick).toHaveBeenCalledWith('start_planning', undefined);
    });

    it('should handle keyboard navigation', async () => {
      const user = userEvent.setup();
      const mockOnActionClick = jest.fn();
      render(
        <QuickActions 
          conversationState={ConversationState.GREETING} 
          onActionClick={mockOnActionClick} 
        />
      );

      const planTripButton = screen.getByText('Plan a trip');
      planTripButton.focus();
      await user.keyboard('{Enter}');

      expect(mockOnActionClick).toHaveBeenCalledWith('start_planning', undefined);
    });

    it('should render no actions for unknown state', () => {
      const mockOnActionClick = jest.fn();
      // Cast to avoid TypeScript error for unknown state
      render(
        <QuickActions 
          conversationState={'unknown_state' as ConversationState} 
          onActionClick={mockOnActionClick} 
        />
      );

      // Should render empty container
      const container = screen.getByRole('generic');
      expect(container.children).toHaveLength(1); // Just the scroll container
    });
  });

  describe('EnhancedChatMessage Component', () => {
    const baseMessage: ChatMessageType = {
      id: 'msg-1',
      role: 'user',
      content: 'Find flights to Tokyo',
      timestamp: new Date('2024-03-15T10:00:00Z'),
      metadata: {}
    };

    it('should render user message correctly', () => {
      render(<EnhancedChatMessage message={baseMessage} />);

      expect(screen.getByText('Find flights to Tokyo')).toBeInTheDocument();
      expect(screen.getByText('👤')).toBeInTheDocument(); // User icon
      expect(screen.getByText('10:00 AM')).toBeInTheDocument(); // Formatted time
    });

    it('should render agent message correctly', () => {
      const agentMessage: ChatMessageType = {
        ...baseMessage,
        role: 'agent',
        content: 'I found some great flights for you!'
      };

      render(<EnhancedChatMessage message={agentMessage} />);

      expect(screen.getByText('I found some great flights for you!')).toBeInTheDocument();
      expect(screen.getByText('🤖')).toBeInTheDocument(); // Agent icon
    });

    it('should render system message correctly', () => {
      const systemMessage: ChatMessageType = {
        ...baseMessage,
        role: 'system',
        content: 'System notification'
      };

      render(<EnhancedChatMessage message={systemMessage} />);

      expect(screen.getByText('System notification')).toBeInTheDocument();
      expect(screen.getByText('⚙️')).toBeInTheDocument(); // System icon
    });

    it('should render metadata for user messages', () => {
      const messageWithMetadata: ChatMessageType = {
        ...baseMessage,
        metadata: {
          intent: {
            type: 'search_flight',
            confidence: 0.9,
            parameters: {}
          },
          entities: [
            { type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }
          ]
        }
      };

      render(<EnhancedChatMessage message={messageWithMetadata} />);

      expect(screen.getByText('Intent:')).toBeInTheDocument();
      expect(screen.getByText('search_flight')).toBeInTheDocument();
      expect(screen.getByText('(90%)')).toBeInTheDocument();
      expect(screen.getByText('Detected:')).toBeInTheDocument();
      expect(screen.getByText('destination: Tokyo')).toBeInTheDocument();
    });

    it('should render suggestions', async () => {
      const user = userEvent.setup();
      const mockOnAction = jest.fn();
      const messageWithSuggestions: ChatMessageType = {
        ...baseMessage,
        role: 'agent',
        content: 'What would you like to do?',
        metadata: {
          suggestions: ['Search flights', 'Find hotels', 'Plan activities']
        }
      };

      render(<EnhancedChatMessage message={messageWithSuggestions} onAction={mockOnAction} />);

      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Search flights')).toBeInTheDocument();
      expect(screen.getByText('Find hotels')).toBeInTheDocument();
      expect(screen.getByText('Plan activities')).toBeInTheDocument();

      // Test suggestion click
      const suggestion = screen.getByText('Search flights');
      await user.click(suggestion);

      expect(mockOnAction).toHaveBeenCalledWith('suggestion', 'Search flights');
    });

    it('should render action required indicator', () => {
      const messageWithAction: ChatMessageType = {
        ...baseMessage,
        role: 'agent',
        content: 'Please provide more information',
        metadata: {
          actionRequired: true
        }
      };

      render(<EnhancedChatMessage message={messageWithAction} />);

      expect(screen.getByText('⚠️')).toBeInTheDocument();
      expect(screen.getByText('Action required')).toBeInTheDocument();
    });

    it('should render markdown content', () => {
      const markdownMessage: ChatMessageType = {
        ...baseMessage,
        role: 'agent',
        content: '**Great flights found!** Here are your options:\n\n## Available Flights\n### Option 1\nDirect flight for $850'
      };

      render(<EnhancedChatMessage message={markdownMessage} />);

      // Check for rendered HTML elements
      const container = screen.getByRole('generic');
      expect(container.querySelector('strong')).toBeInTheDocument();
      expect(container.querySelector('h3')).toBeInTheDocument();
      expect(container.querySelector('h4')).toBeInTheDocument();
    });

    it('should render card attachments', () => {
      const mockOnAction = jest.fn();
      const messageWithCard: ChatMessageType = {
        ...baseMessage,
        role: 'agent',
        content: 'Here are your flight options',
        metadata: {
          attachments: [{
            type: 'card',
            url: '',
            metadata: {
              type: 'card',
              cards: [{
                title: 'Test Flight',
                subtitle: 'NYC → Tokyo',
                details: { 'Price': '$850' },
                actions: [
                  { label: 'Add to Plan', action: 'add_to_plan', data: {} }
                ]
              }]
            }
          }]
        }
      };

      render(<EnhancedChatMessage message={messageWithCard} onAction={mockOnAction} />);

      expect(screen.getByText('Test Flight')).toBeInTheDocument();
      expect(screen.getByText('NYC → Tokyo')).toBeInTheDocument();
      expect(screen.getByText('$850')).toBeInTheDocument();
    });

    it('should format timestamps correctly', () => {
      const morningMessage: ChatMessageType = {
        ...baseMessage,
        timestamp: new Date('2024-03-15T09:30:00Z')
      };

      const eveningMessage: ChatMessageType = {
        ...baseMessage,
        timestamp: new Date('2024-03-15T21:45:00Z')
      };

      const { rerender } = render(<EnhancedChatMessage message={morningMessage} />);
      expect(screen.getByText('9:30 AM')).toBeInTheDocument();

      rerender(<EnhancedChatMessage message={eveningMessage} />);
      expect(screen.getByText('9:45 PM')).toBeInTheDocument();
    });

    it('should apply correct CSS classes based on message role', () => {
      const { container, rerender } = render(<EnhancedChatMessage message={baseMessage} />);
      
      expect(container.firstChild).toHaveClass('enhanced-chat-message', 'user');

      const agentMessage: ChatMessageType = {
        ...baseMessage,
        role: 'agent'
      };

      rerender(<EnhancedChatMessage message={agentMessage} />);
      expect(container.firstChild).toHaveClass('enhanced-chat-message', 'agent');
    });
  });

  describe('Component Integration', () => {
    it('should handle complex conversation with multiple components', async () => {
      const user = userEvent.setup();
      const mockOnAction = jest.fn();

      // Create a conversation with multiple message types
      const messages: ChatMessageType[] = [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Find flights to Tokyo',
          timestamp: new Date(),
          metadata: {
            intent: { type: 'search_flight', confidence: 0.9, parameters: {} },
            entities: [{ type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] }]
          }
        },
        {
          id: 'msg-2',
          role: 'agent',
          content: 'I found some great flights!',
          timestamp: new Date(),
          metadata: {
            attachments: [{
              type: 'card',
              url: '',
              metadata: {
                type: 'card',
                cards: [{
                  title: 'ANA Flight',
                  subtitle: 'JFK → NRT',
                  details: { 'Price': '$850' },
                  actions: [
                    { label: 'Add to Plan', action: 'add_to_plan', data: { id: 'flight-1' } }
                  ]
                }]
              }
            }]
          }
        },
        {
          id: 'msg-3',
          role: 'agent',
          content: 'Would you like to add any of these to your plan?',
          timestamp: new Date(),
          metadata: {
            suggestions: ['Add flight to plan', 'Search for hotels', 'Compare prices']
          }
        }
      ];

      const TestConversation = () => (
        <div>
          {messages.map(message => (
            <EnhancedChatMessage 
              key={message.id} 
              message={message} 
              onAction={mockOnAction} 
            />
          ))}
          <QuickActions 
            conversationState={ConversationState.PRESENTING_OPTIONS}
            onActionClick={mockOnAction}
          />
        </div>
      );

      render(<TestConversation />);

      // Verify all messages rendered
      expect(screen.getByText('Find flights to Tokyo')).toBeInTheDocument();
      expect(screen.getByText('I found some great flights!')).toBeInTheDocument();
      expect(screen.getByText('ANA Flight')).toBeInTheDocument();
      expect(screen.getByText('Would you like to add any of these to your plan?')).toBeInTheDocument();

      // Test card action
      const addToPlanButton = screen.getByText('Add to Plan');
      await user.click(addToPlanButton);
      expect(mockOnAction).toHaveBeenCalledWith('add_to_plan', { id: 'flight-1' });

      // Test suggestion
      const suggestion = screen.getByText('Add flight to plan');
      await user.click(suggestion);
      expect(mockOnAction).toHaveBeenCalledWith('suggestion', 'Add flight to plan');

      // Test quick action
      const sortByPrice = screen.getByText('Sort by price');
      await user.click(sortByPrice);
      expect(mockOnAction).toHaveBeenCalledWith('sort_price', undefined);
    });

    it('should handle accessibility requirements', () => {
      const message: ChatMessageType = {
        id: 'msg-1',
        role: 'agent',
        content: 'Flight search results',
        timestamp: new Date(),
        metadata: {
          attachments: [{
            type: 'card',
            url: '',
            metadata: {
              type: 'card',
              cards: [{
                title: 'Test Flight',
                subtitle: 'Test Route',
                details: { 'Price': '$500' },
                actions: [
                  { label: 'Add to Plan', action: 'add_to_plan', data: {} }
                ]
              }]
            }
          }]
        }
      };

      render(
        <div>
          <EnhancedChatMessage message={message} />
          <QuickActions 
            conversationState={ConversationState.GREETING}
            onActionClick={jest.fn()}
          />
        </div>
      );

      // Check for proper button elements (accessible by default)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);

      // All buttons should be focusable
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('should handle responsive behavior', () => {
      // Mock window resize
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      const message: ChatMessageType = {
        id: 'msg-1',
        role: 'agent',
        content: 'Test message',
        timestamp: new Date(),
        metadata: {}
      };

      const { container } = render(
        <div>
          <EnhancedChatMessage message={message} />
          <QuickActions 
            conversationState={ConversationState.GREETING}
            onActionClick={jest.fn()}
          />
        </div>
      );

      // Components should render without errors on mobile viewport
      expect(container).toBeInTheDocument();
    });
  });
});