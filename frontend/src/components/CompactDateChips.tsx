import React, { useState } from 'react';
import { addDays, formatDate } from '../utils/dateHelpers';
import '../styles/components/CompactDateChips.css';

interface CompactDateChipsProps {
  onDateSelect: (dates: DateSelection) => void;
  onClose: () => void;
  context: 'flight' | 'hotel' | 'general';
  disabled?: boolean;
}

interface DateSelection {
  startDate: string;
  endDate: string;
  startLabel: string;
  endLabel: string;
  type: 'flight' | 'hotel' | 'general';
}

interface QuickDateOption {
  label: string;
  getStartDate: () => Date;
  getEndDate: () => Date;
  description: string;
}

const CompactDateChips: React.FC<CompactDateChipsProps> = ({
  onDateSelect,
  onClose,
  context,
  disabled = false
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const getQuickDateOptions = (): QuickDateOption[] => {
    const today = new Date();
    
    const getNextWeekend = () => {
      const currentDay = today.getDay(); // 0=Sunday, 1=Monday, ..., 5=Friday, 6=Saturday
      let daysToAdd = 0;
      
      if (currentDay === 0) { // Sunday
        daysToAdd = 5; // Go to next Friday
      } else if (currentDay === 1) { // Monday
        daysToAdd = 4; // Go to Friday
      } else if (currentDay === 2) { // Tuesday
        daysToAdd = 3; // Go to Friday
      } else if (currentDay === 3) { // Wednesday
        daysToAdd = 2; // Go to Friday
      } else if (currentDay === 4) { // Thursday
        daysToAdd = 1; // Go to Friday
      } else if (currentDay === 5) { // Friday
        daysToAdd = 0; // Today is Friday
      } else if (currentDay === 6) { // Saturday
        daysToAdd = 6; // Go to next Friday
      }
      
      return addDays(today, daysToAdd);
    };

    const options: QuickDateOption[] = [
      {
        label: 'Today',
        getStartDate: () => new Date(today.getTime()), // Use getTime() for proper cloning
        getEndDate: () => context === 'hotel' ? addDays(today, 1) : addDays(today, 3),
        description: context === 'hotel' ? 'Today - Tomorrow' : 'Today - 3 days'
      },
      {
        label: 'Tomorrow',
        getStartDate: () => addDays(today, 1),
        getEndDate: () => context === 'hotel' ? addDays(today, 2) : addDays(today, 4),
        description: context === 'hotel' ? 'Tomorrow - Day after' : 'Tomorrow - 3 days'
      },
      {
        label: 'This Weekend',
        getStartDate: () => getNextWeekend(),
        getEndDate: () => addDays(getNextWeekend(), 2),
        description: 'Fri - Sun'
      },
      {
        label: 'Next Week',
        getStartDate: () => addDays(today, 7),
        getEndDate: () => addDays(today, 10),
        description: '1 week - 3 days'
      },
      {
        label: 'Next Month',
        getStartDate: () => addDays(today, 30),
        getEndDate: () => addDays(today, 37),
        description: '1 month - 1 week'
      }
    ];

    return options;
  };

  const handleQuickSelect = (option: QuickDateOption) => {
    if (disabled) return;

    setSelectedOption(option.label);
    
    try {
      const startDate = option.getStartDate();
      const endDate = option.getEndDate();
      
      const dateSelection: DateSelection = {
        startDate: formatDate(startDate, 'iso'),
        endDate: formatDate(endDate, 'iso'),
        startLabel: formatDate(startDate, 'short'),
        endLabel: formatDate(endDate, 'short'),
        type: context
      };

      // Slight delay for visual feedback
      setTimeout(() => {
        onDateSelect(dateSelection);
      }, 150);
    } catch (error) {
      console.error('Error in handleQuickSelect:', error);
    }
  };

  const getContextLabels = () => {
    switch (context) {
      case 'flight':
        return { start: 'Departure', end: 'Return' };
      case 'hotel':
        return { start: 'Check-in', end: 'Check-out' };
      default:
        return { start: 'Start', end: 'End' };
    }
  };

  const getContextEmoji = () => {
    switch (context) {
      case 'flight':
        return '✈️';
      case 'hotel':
        return '🏨';
      default:
        return '📅';
    }
  };

  const labels = getContextLabels();
  const emoji = getContextEmoji();

  return (
    <div className="compact-date-chips">
      <div className="date-chips-header">
        <div className="date-chips-title">
          <span className="context-emoji">{emoji}</span>
          <span className="context-text">
            Select {labels.start} & {labels.end} Dates
          </span>
        </div>
        <button 
          onClick={onClose}
          className="close-chips-btn"
          aria-label="Close date selection"
          disabled={disabled}
        >
          ✕
        </button>
      </div>

      <div className="date-chips-grid">
        {getQuickDateOptions().map((option) => (
          <button
            key={option.label}
            onClick={() => handleQuickSelect(option)}
            disabled={disabled}
            className={`date-chip ${selectedOption === option.label ? 'selected' : ''}`}
            aria-label={`Select ${option.label}: ${option.description}`}
          >
            <div className="chip-main-label">{option.label}</div>
            <div className="chip-description">{option.description}</div>
          </button>
        ))}
      </div>

      <div className="date-chips-footer">
        <span className="helper-text">
          Tap any option to select {labels.start.toLowerCase()} and {labels.end.toLowerCase()} dates automatically
        </span>
      </div>
    </div>
  );
};

export default CompactDateChips;