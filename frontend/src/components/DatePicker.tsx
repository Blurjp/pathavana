import React, { useState, useRef, useEffect } from 'react';
import { formatDate, parseDateInput, addDays } from '../utils/dateHelpers';

interface DatePickerProps {
  value?: string;
  placeholder?: string;
  onChange: (date: string) => void;
  onClose?: () => void;
  label?: string;
  type?: 'departure' | 'return' | 'checkin' | 'checkout' | 'general';
  minDate?: string;
  maxDate?: string;
  disabled?: boolean;
}

const DatePicker: React.FC<DatePickerProps> = ({
  value,
  placeholder = 'Select date',
  onChange,
  onClose,
  label,
  type = 'general',
  minDate,
  maxDate,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value || '');
  const [selectedDate, setSelectedDate] = useState<Date | null>(
    value ? parseDateInput(value) : null
  );
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Get current date for calendar display
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(
    selectedDate || today
  );

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleClose = () => {
    setIsOpen(false);
    onClose?.();
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    const dateString = formatDate(date, 'iso');
    setInputValue(formatDate(date, 'short'));
    onChange(dateString);
    handleClose();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Try to parse the input
    const parsed = parseDateInput(value);
    if (parsed) {
      setSelectedDate(parsed);
      onChange(formatDate(parsed, 'iso'));
    }
  };

  const getCalendarDays = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    // First day of the month
    const firstDay = new Date(year, month, 1);
    // Last day of the month
    const lastDay = new Date(year, month + 1, 0);
    
    // Days from previous month to fill the first week
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - firstDay.getDay());
    
    // Days to show (6 weeks)
    const days = [];
    const currentDate = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      days.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return days;
  };

  const isDateDisabled = (date: Date) => {
    if (disabled) return true;
    
    const dateStr = formatDate(date, 'iso');
    
    if (minDate && dateStr < minDate) return true;
    if (maxDate && dateStr > maxDate) return true;
    
    // For return dates, must be after departure
    if (type === 'return' && minDate && dateStr <= minDate) return true;
    
    return false;
  };

  const isDateSelected = (date: Date) => {
    return selectedDate && 
           date.getFullYear() === selectedDate.getFullYear() &&
           date.getMonth() === selectedDate.getMonth() &&
           date.getDate() === selectedDate.getDate();
  };

  const isToday = (date: Date) => {
    return date.getFullYear() === today.getFullYear() &&
           date.getMonth() === today.getMonth() &&
           date.getDate() === today.getDate();
  };

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentMonth.getMonth();
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(currentMonth);
    if (direction === 'prev') {
      newMonth.setMonth(newMonth.getMonth() - 1);
    } else {
      newMonth.setMonth(newMonth.getMonth() + 1);
    }
    setCurrentMonth(newMonth);
  };

  const getQuickDates = () => {
    const quickDates = [];
    
    if (type === 'departure' || type === 'checkin') {
      quickDates.push(
        { label: 'Today', date: today },
        { label: 'Tomorrow', date: addDays(today, 1) },
        { label: 'Next Week', date: addDays(today, 7) },
        { label: 'Next Month', date: addDays(today, 30) }
      );
    } else if (type === 'return' || type === 'checkout') {
      const baseDays = minDate ? 1 : 0;
      quickDates.push(
        { label: '3 days', date: addDays(minDate ? new Date(minDate) : today, 3 + baseDays) },
        { label: '1 week', date: addDays(minDate ? new Date(minDate) : today, 7 + baseDays) },
        { label: '2 weeks', date: addDays(minDate ? new Date(minDate) : today, 14 + baseDays) },
        { label: '1 month', date: addDays(minDate ? new Date(minDate) : today, 30 + baseDays) }
      );
    }
    
    return quickDates;
  };

  const getTypeLabel = () => {
    switch (type) {
      case 'departure': return 'Departure Date';
      case 'return': return 'Return Date';
      case 'checkin': return 'Check-in Date';
      case 'checkout': return 'Check-out Date';
      default: return label || 'Select Date';
    }
  };

  return (
    <div className="date-picker">
      <div className="date-picker-input-group">
        {label && <label className="date-picker-label">{getTypeLabel()}</label>}
        <div className="date-picker-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
            disabled={disabled}
            className="date-picker-input"
            autoComplete="off"
          />
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            disabled={disabled}
            className="date-picker-toggle"
            aria-label="Open calendar"
          >
            📅
          </button>
        </div>
      </div>

      {isOpen && (
        <div ref={dropdownRef} className="date-picker-dropdown">
          {/* Quick date selection */}
          <div className="date-picker-quick-dates">
            {getQuickDates().map((quick, index) => (
              <button
                key={index}
                onClick={() => handleDateSelect(quick.date)}
                disabled={isDateDisabled(quick.date)}
                className="date-picker-quick-btn"
              >
                {quick.label}
              </button>
            ))}
          </div>

          {/* Calendar header */}
          <div className="date-picker-header">
            <button
              onClick={() => navigateMonth('prev')}
              className="date-picker-nav"
              aria-label="Previous month"
            >
              ‹
            </button>
            <span className="date-picker-month">
              {currentMonth.toLocaleDateString('en-US', { 
                month: 'long', 
                year: 'numeric' 
              })}
            </span>
            <button
              onClick={() => navigateMonth('next')}
              className="date-picker-nav"
              aria-label="Next month"
            >
              ›
            </button>
          </div>

          {/* Calendar grid */}
          <div className="date-picker-calendar">
            <div className="date-picker-weekdays">
              {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                <div key={day} className="date-picker-weekday">
                  {day}
                </div>
              ))}
            </div>
            <div className="date-picker-days">
              {getCalendarDays().map((date, index) => (
                <button
                  key={index}
                  onClick={() => handleDateSelect(date)}
                  disabled={isDateDisabled(date)}
                  className={`
                    date-picker-day
                    ${isDateSelected(date) ? 'selected' : ''}
                    ${isToday(date) ? 'today' : ''}
                    ${!isCurrentMonth(date) ? 'other-month' : ''}
                    ${isDateDisabled(date) ? 'disabled' : ''}
                  `}
                >
                  {date.getDate()}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatePicker;