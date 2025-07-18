import React, { useState, useEffect } from 'react';
import CompactDateChips from './CompactDateChips';
import '../styles/components/SmartPrompts.css';

interface SmartPromptsProps {
  lastMessage?: string;
  metadata?: any;
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

interface DateSelection {
  startDate: string;
  endDate: string;
  startLabel: string;
  endLabel: string;
  type: 'flight' | 'hotel' | 'general';
}

const SmartPrompts: React.FC<SmartPromptsProps> = ({
  lastMessage = '',
  metadata,
  onSendMessage,
  disabled = false
}) => {
  const [showDateChips, setShowDateChips] = useState(false);
  const [dateContext, setDateContext] = useState<'flight' | 'hotel' | 'general'>('general');
  
  // Detect when AI is asking for travel dates
  useEffect(() => {
    const messageText = lastMessage.toLowerCase();
    
    // Only show date picker for explicit date requests
    const hasDateRequest = 
      messageText.includes('when would you like') ||
      messageText.includes('what dates') ||
      messageText.includes('when are you planning') ||
      messageText.includes('travel dates') ||
      messageText.includes('departure date') ||
      messageText.includes('return date') ||
      messageText.includes('check-in date') ||
      messageText.includes('check-out date') ||
      (messageText.includes('when') && (messageText.includes('travel') || messageText.includes('trip')));

    if (hasDateRequest) {
      // Determine context based on message content - be more specific
      let context: 'flight' | 'hotel' | 'general' = 'general';
      
      // Only set flight context if explicitly about flights
      if (messageText.includes('flight') || 
          messageText.includes('departure') || 
          messageText.includes('return') ||
          messageText.includes('flying')) {
        context = 'flight';
      } 
      // Only set hotel context if explicitly about hotels/accommodation
      else if (messageText.includes('hotel') || 
               messageText.includes('accommodation') ||
               messageText.includes('check-in') || 
               messageText.includes('check-out') ||
               messageText.includes('stay') ||
               messageText.includes('booking')) {
        context = 'hotel';
      }
      
      setDateContext(context);
      setShowDateChips(true);
    } else {
      setShowDateChips(false);
    }
  }, [lastMessage]);

  const handleDateSelect = (dates: DateSelection) => {
    // Generate natural language message based on context
    let message = '';
    
    if (dates.type === 'flight') {
      message = `I want to depart on ${dates.startLabel} and return on ${dates.endLabel}`;
    } else if (dates.type === 'hotel') {
      message = `I want to check in on ${dates.startLabel} and check out on ${dates.endLabel}`;
    } else {
      message = `I want to travel from ${dates.startLabel} to ${dates.endLabel}`;
    }
    
    onSendMessage(message);
    setShowDateChips(false);
  };

  const handleClose = () => {
    setShowDateChips(false);
  };

  if (!showDateChips) {
    return null;
  }

  return (
    <CompactDateChips
      onDateSelect={handleDateSelect}
      onClose={handleClose}
      context={dateContext}
      disabled={disabled}
    />
  );
};

export default SmartPrompts;