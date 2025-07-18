import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CompactDateChips from '../components/CompactDateChips';
import SmartPrompts from '../components/SmartPrompts';

describe('Fixed UI Components Test', () => {
  describe('CompactDateChips', () => {
    const mockOnDateSelect = jest.fn();
    const mockOnClose = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
    });

    test('renders compact date chips with reduced size', () => {
      render(
        <CompactDateChips
          onDateSelect={mockOnDateSelect}
          onClose={mockOnClose}
          context="general"
          disabled={false}
        />
      );

      // Check if the component renders
      expect(screen.getByText('Select Start & End Dates')).toBeInTheDocument();
      
      // Check for quick date options
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Tomorrow')).toBeInTheDocument();
      expect(screen.getByText('This Weekend')).toBeInTheDocument();
      expect(screen.getByText('Next Week')).toBeInTheDocument();
      expect(screen.getByText('Next Month')).toBeInTheDocument();
    });

    test('quick date options are clickable and call onDateSelect', async () => {
      render(
        <CompactDateChips
          onDateSelect={mockOnDateSelect}
          onClose={mockOnClose}
          context="flight"
          disabled={false}
        />
      );

      // Click on "Today" option
      const todayButton = screen.getByText('Today');
      fireEvent.click(todayButton);

      // Wait for the timeout in handleQuickSelect
      await waitFor(() => {
        expect(mockOnDateSelect).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'flight',
            startDate: expect.any(String),
            endDate: expect.any(String),
            startLabel: expect.any(String),
            endLabel: expect.any(String)
          })
        );
      }, { timeout: 200 });
    });

    test('shows flight context labels correctly', () => {
      render(
        <CompactDateChips
          onDateSelect={mockOnDateSelect}
          onClose={mockOnClose}
          context="flight"
          disabled={false}
        />
      );

      expect(screen.getByText('Select Departure & Return Dates')).toBeInTheDocument();
      expect(screen.getByText('✈️')).toBeInTheDocument();
    });

    test('shows hotel context labels correctly', () => {
      render(
        <CompactDateChips
          onDateSelect={mockOnDateSelect}
          onClose={mockOnClose}
          context="hotel"
          disabled={false}
        />
      );

      expect(screen.getByText('Select Check-in & Check-out Dates')).toBeInTheDocument();
      expect(screen.getByText('🏨')).toBeInTheDocument();
    });

    test('close button works', () => {
      render(
        <CompactDateChips
          onDateSelect={mockOnDateSelect}
          onClose={mockOnClose}
          context="general"
          disabled={false}
        />
      );

      const closeButton = screen.getByLabelText('Close date selection');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('SmartPrompts Context Detection', () => {
    const mockOnSendMessage = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
    });

    test('does not show date picker for non-date messages', () => {
      render(
        <SmartPrompts
          lastMessage="Hello, how can I help you?"
          onSendMessage={mockOnSendMessage}
          disabled={false}
        />
      );

      // Should not render anything (returns null)
      expect(screen.queryByText('Select')).not.toBeInTheDocument();
    });

    test('shows general date picker for general date requests', () => {
      render(
        <SmartPrompts
          lastMessage="When would you like to travel?"
          onSendMessage={mockOnSendMessage}
          disabled={false}
        />
      );

      // Should show date picker with general context
      expect(screen.getByText('Select Start & End Dates')).toBeInTheDocument();
      expect(screen.getByText('📅')).toBeInTheDocument();
    });

    test('shows flight context for flight-related messages', () => {
      render(
        <SmartPrompts
          lastMessage="When would you like to depart on your flight?"
          onSendMessage={mockOnSendMessage}
          disabled={false}
        />
      );

      // Should show date picker with flight context
      expect(screen.getByText('Select Departure & Return Dates')).toBeInTheDocument();
      expect(screen.getByText('✈️')).toBeInTheDocument();
    });

    test('shows hotel context only for hotel-related messages', () => {
      render(
        <SmartPrompts
          lastMessage="When would you like to check in to your hotel?"
          onSendMessage={mockOnSendMessage}
          disabled={false}
        />
      );

      // Should show date picker with hotel context
      expect(screen.getByText('Select Check-in & Check-out Dates')).toBeInTheDocument();
      expect(screen.getByText('🏨')).toBeInTheDocument();
    });

    test('does not show hotel context for general travel questions', () => {
      render(
        <SmartPrompts
          lastMessage="When would you like to travel to Paris?"
          onSendMessage={mockOnSendMessage}
          disabled={false}
        />
      );

      // Should show general context, not hotel
      expect(screen.getByText('Select Start & End Dates')).toBeInTheDocument();
      expect(screen.getByText('📅')).toBeInTheDocument();
      expect(screen.queryByText('Select Check-in & Check-out Dates')).not.toBeInTheDocument();
    });
  });
});