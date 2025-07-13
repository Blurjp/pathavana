import React from 'react';
import { QuickAction, ConversationState } from '../../types/AIAgentTypes';
import './QuickActions.css';

interface QuickActionsProps {
  conversationState: ConversationState;
  onActionClick: (action: string, context?: any) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ 
  conversationState, 
  onActionClick 
}) => {
  const quickActionsMap: Record<ConversationState, QuickAction[]> = {
    [ConversationState.GREETING]: [
      { label: "Plan a trip", icon: "✈️", action: "start_planning" },
      { label: "View my plans", icon: "📋", action: "view_plans" },
      { label: "Check bookings", icon: "🎫", action: "view_bookings" }
    ],
    [ConversationState.GATHERING_REQUIREMENTS]: [
      { label: "Popular destinations", icon: "🌍", action: "show_destinations" },
      { label: "Budget calculator", icon: "💰", action: "budget_tool" },
      { label: "Travel dates", icon: "📅", action: "date_picker" }
    ],
    [ConversationState.SEARCHING]: [
      { label: "Change dates", icon: "📅", action: "modify_dates" },
      { label: "Filter results", icon: "🔍", action: "add_filters" },
      { label: "Compare options", icon: "⚖️", action: "compare" }
    ],
    [ConversationState.PRESENTING_OPTIONS]: [
      { label: "Sort by price", icon: "💲", action: "sort_price" },
      { label: "Sort by rating", icon: "⭐", action: "sort_rating" },
      { label: "Show more", icon: "➕", action: "load_more" }
    ],
    [ConversationState.REFINING_SEARCH]: [
      { label: "Reset filters", icon: "🔄", action: "reset_filters" },
      { label: "Save search", icon: "💾", action: "save_search" },
      { label: "New search", icon: "🆕", action: "new_search" }
    ],
    [ConversationState.ADDING_TO_PLAN]: [
      { label: "View plan", icon: "👁️", action: "view_current_plan" },
      { label: "Budget status", icon: "📊", action: "check_budget" },
      { label: "Continue searching", icon: "🔍", action: "continue_search" }
    ],
    [ConversationState.REVIEWING_PLAN]: [
      { label: "Book all", icon: "✅", action: "book_all" },
      { label: "Share plan", icon: "📤", action: "share_plan" },
      { label: "Export PDF", icon: "📄", action: "export_pdf" }
    ],
    [ConversationState.BOOKING]: [
      { label: "Payment info", icon: "💳", action: "payment_details" },
      { label: "Traveler details", icon: "👥", action: "traveler_info" },
      { label: "Review booking", icon: "📋", action: "review_booking" }
    ],
    [ConversationState.POST_BOOKING]: [
      { label: "View tickets", icon: "🎫", action: "view_tickets" },
      { label: "Add to calendar", icon: "📅", action: "add_calendar" },
      { label: "Plan another trip", icon: "✈️", action: "new_trip" }
    ]
  };

  const currentActions = quickActionsMap[conversationState] || [];

  return (
    <div className="quick-actions-container">
      <div className="quick-actions-scroll">
        {currentActions.map((action, index) => (
          <button
            key={index}
            className="quick-action-btn"
            onClick={() => onActionClick(action.action, action.context)}
            title={action.label}
          >
            <span className="quick-action-icon">{action.icon}</span>
            <span className="quick-action-label">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};