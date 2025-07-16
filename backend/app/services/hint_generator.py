"""
Dynamic hint generation system for travel planning assistance.

This module provides contextual hints based on conversation state and user intent
to help travelers make better decisions and create comprehensive travel plans.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from ..core.logger import logger


class ConversationState(Enum):
    """Represents the current state of the travel planning conversation."""
    INITIAL = "initial"
    DESTINATION_SELECTION = "destination_selection"
    DATE_SELECTION = "date_selection"
    HOTEL_SEARCH = "hotel_search"
    FLIGHT_SEARCH = "flight_search"
    ACTIVITY_PLANNING = "activity_planning"
    BUDGET_DISCUSSION = "budget_discussion"
    FINALIZATION = "finalization"
    COMPLETED = "completed"


class TravelEntity:
    """Represents a travel-related entity extracted from conversation."""
    def __init__(self, entity_type: str, value: str, confidence: float = 1.0):
        self.type = entity_type
        self.value = value
        self.confidence = confidence


class DynamicHintGenerator:
    """Generates contextual hints for travel planning conversations."""
    
    def __init__(self):
        self.destination_patterns = [
            (r'\b(paris|france|eiffel tower)\b', 'Paris', 'city'),
            (r'\b(tokyo|japan|shibuya)\b', 'Tokyo', 'city'),
            (r'\b(bali|indonesia|ubud)\b', 'Bali', 'region'),
            (r'\b(new york|nyc|manhattan|brooklyn)\b', 'New York', 'city'),
            (r'\b(london|uk|england|big ben)\b', 'London', 'city'),
            (r'\b(barcelona|spain|sagrada familia)\b', 'Barcelona', 'city'),
            (r'\b(rome|italy|colosseum)\b', 'Rome', 'city'),
            (r'\b(dubai|uae|burj khalifa)\b', 'Dubai', 'city'),
            (r'\b(singapore|marina bay)\b', 'Singapore', 'city'),
            (r'\b(patagonia|chile|argentina)\b', 'Patagonia', 'region'),
            (r'\b(french riviera|nice|cannes|monaco)\b', 'French Riviera', 'region'),
        ]
        
        self.date_patterns = [
            (r'\b(tomorrow)\b', 'tomorrow', 'relative'),
            (r'\b(next week)\b', 'next_week', 'relative'),
            (r'\b(next month)\b', 'next_month', 'relative'),
            (r'\b(this weekend)\b', 'this_weekend', 'relative'),
            (r'\b(in (\d+) days?)\b', 'days_from_now', 'relative'),
            (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', 'month', 'absolute'),
            (r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b', 'date', 'absolute'),
            (r'\b(summer|winter|spring|fall|autumn)\b', 'season', 'seasonal'),
        ]
        
        self.activity_keywords = [
            'museum', 'tour', 'restaurant', 'beach', 'hiking', 'shopping',
            'nightlife', 'culture', 'history', 'adventure', 'relaxation',
            'food', 'wine', 'art', 'nature', 'photography', 'sports'
        ]
        
        self.budget_indicators = [
            (r'\b(budget|cheap|affordable|economical)\b', 'budget'),
            (r'\b(mid-range|moderate|reasonable)\b', 'mid-range'),
            (r'\b(luxury|premium|high-end|expensive)\b', 'luxury'),
            (r'\$(\d+)', 'specific_amount'),
        ]
    
    def analyze_conversation_state(self, conversation_history: List[Dict], current_context: Dict) -> ConversationState:
        """Determine the current state of the conversation."""
        if not conversation_history:
            return ConversationState.INITIAL
        
        # Check what information we have
        has_destination = bool(current_context.get('destination'))
        has_dates = bool(current_context.get('dates'))
        has_hotel = bool(current_context.get('selected_items', {}).get('hotels'))
        has_flight = bool(current_context.get('selected_items', {}).get('flights'))
        
        # Analyze recent messages
        try:
            if conversation_history and isinstance(conversation_history, list):
                recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
                recent_text = ' '.join([msg.get('content', '') for msg in recent_messages if isinstance(msg, dict)]).lower()
            else:
                recent_text = ""
        except Exception:
            recent_text = ""
        
        # Determine state based on context and recent conversation
        if 'hotel' in recent_text and has_destination:
            return ConversationState.HOTEL_SEARCH
        elif 'flight' in recent_text and has_destination:
            return ConversationState.FLIGHT_SEARCH
        elif any(activity in recent_text for activity in self.activity_keywords):
            return ConversationState.ACTIVITY_PLANNING
        elif any(budget in recent_text for budget in ['budget', 'cost', 'price', 'expensive']):
            return ConversationState.BUDGET_DISCUSSION
        elif not has_destination:
            return ConversationState.DESTINATION_SELECTION
        elif not has_dates:
            return ConversationState.DATE_SELECTION
        elif has_destination and has_dates and (has_hotel or has_flight):
            return ConversationState.FINALIZATION
        
        return ConversationState.INITIAL
    
    def extract_entities(self, message: str) -> List[TravelEntity]:
        """Extract travel-related entities from the message."""
        entities = []
        message_lower = message.lower()
        
        # Extract destinations
        for pattern, destination, dest_type in self.destination_patterns:
            if re.search(pattern, message_lower):
                entities.append(TravelEntity('destination', destination, 0.9))
        
        # Extract dates
        for pattern, date_type, date_category in self.date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = match.group(0) if date_category != 'days_from_now' else match.group(1)
                entities.append(TravelEntity('date', value, 0.8))
        
        # Extract activities
        for activity in self.activity_keywords:
            if activity in message_lower:
                entities.append(TravelEntity('activity', activity, 0.7))
        
        # Extract budget preferences
        for pattern, budget_type in self.budget_indicators:
            if re.search(pattern, message_lower):
                entities.append(TravelEntity('budget', budget_type, 0.8))
        
        return entities
    
    def generate_hints(self, 
                      message: str,
                      conversation_state: ConversationState,
                      current_context: Dict,
                      entities: List[TravelEntity]) -> List[Dict[str, str]]:
        """Generate contextual hints based on the current state and entities."""
        hints = []
        
        # State-specific hints
        if conversation_state == ConversationState.INITIAL:
            hints.extend([
                {
                    "type": "suggestion",
                    "text": "Start by telling me your dream destination",
                    "action": "prompt_destination"
                },
                {
                    "type": "tip",
                    "text": "Consider mentioning your travel dates and group size",
                    "action": "collect_basic_info"
                }
            ])
        
        elif conversation_state == ConversationState.DESTINATION_SELECTION:
            if not current_context.get('destination'):
                hints.extend([
                    {
                        "type": "suggestion",
                        "text": "Popular destinations this season",
                        "action": "show_trending_destinations"
                    },
                    {
                        "type": "question",
                        "text": "Are you looking for beaches, cities, or mountains?",
                        "action": "filter_by_type"
                    }
                ])
        
        elif conversation_state == ConversationState.DATE_SELECTION:
            hints.extend([
                {
                    "type": "tip",
                    "text": "Flexible dates can save you up to 30% on flights",
                    "action": "show_flexible_dates"
                },
                {
                    "type": "suggestion",
                    "text": "Check the best season for " + current_context.get('destination', 'your destination'),
                    "action": "show_seasonal_info"
                }
            ])
        
        elif conversation_state == ConversationState.HOTEL_SEARCH:
            destination = current_context.get('destination', 'your destination')
            hints.extend([
                {
                    "type": "filter",
                    "text": "Filter by amenities (pool, gym, spa)",
                    "action": "apply_hotel_filters"
                },
                {
                    "type": "tip",
                    "text": f"Best neighborhoods in {destination} for tourists",
                    "action": "show_neighborhood_guide"
                }
            ])
        
        elif conversation_state == ConversationState.FLIGHT_SEARCH:
            hints.extend([
                {
                    "type": "tip",
                    "text": "Book flights 6-8 weeks in advance for best prices",
                    "action": "show_price_trends"
                },
                {
                    "type": "suggestion",
                    "text": "Consider nearby airports for better deals",
                    "action": "show_alternative_airports"
                }
            ])
        
        elif conversation_state == ConversationState.ACTIVITY_PLANNING:
            # Add activity-specific hints based on extracted entities
            activities = [e.value for e in entities if e.type == 'activity']
            if activities:
                for activity in activities[:2]:  # Limit to 2 activity hints
                    hints.append({
                        "type": "recommendation",
                        "text": f"Top-rated {activity} experiences",
                        "action": f"show_{activity}_options"
                    })
            else:
                hints.append({
                    "type": "suggestion",
                    "text": "Discover must-do activities",
                    "action": "show_popular_activities"
                })
        
        elif conversation_state == ConversationState.BUDGET_DISCUSSION:
            budget_type = next((e.value for e in entities if e.type == 'budget'), 'mid-range')
            hints.extend([
                {
                    "type": "calculator",
                    "text": f"Estimate total cost for {budget_type} trip",
                    "action": "show_cost_breakdown"
                },
                {
                    "type": "tip",
                    "text": "Ways to save money without compromising experience",
                    "action": "show_savings_tips"
                }
            ])
        
        elif conversation_state == ConversationState.FINALIZATION:
            hints.extend([
                {
                    "type": "checklist",
                    "text": "Pre-trip checklist",
                    "action": "show_preparation_checklist"
                },
                {
                    "type": "action",
                    "text": "Save and share your itinerary",
                    "action": "save_itinerary"
                }
            ])
        
        # Add entity-based hints
        if any(e.type == 'destination' for e in entities):
            destination = next((e.value for e in entities if e.type == 'destination'), None)
            if destination:
                hints.append({
                    "type": "info",
                    "text": f"Essential travel info for {destination}",
                    "action": f"show_{destination.lower().replace(' ', '_')}_guide"
                })
        
        # Limit hints to avoid overwhelming the user
        return hints[:4]
    
    def create_response_with_hints(self,
                                   message: str,
                                   conversation_history: List[Dict],
                                   current_context: Dict,
                                   base_response: str) -> Dict[str, Any]:
        """Create a complete response with contextual hints."""
        # Analyze current state
        state = self.analyze_conversation_state(conversation_history, current_context)
        
        # Extract entities from the message
        entities = self.extract_entities(message)
        
        # Generate hints
        hints = self.generate_hints(message, state, current_context, entities)
        
        # Create structured response
        response = {
            "content": base_response,
            "hints": hints,
            "conversation_state": state.value,
            "extracted_entities": [
                {"type": e.type, "value": e.value, "confidence": e.confidence}
                for e in entities
            ],
            "context_summary": self._create_context_summary(current_context),
            "next_steps": self._suggest_next_steps(state, current_context)
        }
        
        return response
    
    def _create_context_summary(self, context: Dict) -> Dict[str, Any]:
        """Create a summary of the current trip context."""
        summary = {}
        
        if context.get('destination'):
            summary['destination'] = context['destination']
        
        if context.get('dates'):
            summary['travel_dates'] = context['dates']
        
        if context.get('travelers'):
            summary['group_size'] = context['travelers']
        
        if context.get('budget'):
            summary['budget_preference'] = context['budget']
        
        selected_items = context.get('selected_items', {})
        if selected_items:
            summary['selections'] = {
                'hotels': len(selected_items.get('hotels', [])),
                'flights': len(selected_items.get('flights', [])),
                'activities': len(selected_items.get('activities', []))
            }
        
        return summary
    
    def _suggest_next_steps(self, state: ConversationState, context: Dict) -> List[str]:
        """Suggest next steps based on current state."""
        steps = []
        
        if state == ConversationState.INITIAL:
            steps.append("Tell me where you'd like to go")
        elif state == ConversationState.DESTINATION_SELECTION:
            steps.append("Choose your destination")
        elif state == ConversationState.DATE_SELECTION:
            steps.append("Select your travel dates")
        elif state == ConversationState.HOTEL_SEARCH:
            steps.append("Find and book your accommodation")
        elif state == ConversationState.FLIGHT_SEARCH:
            steps.append("Search for flights")
        elif state == ConversationState.ACTIVITY_PLANNING:
            steps.append("Plan your activities and experiences")
        elif state == ConversationState.BUDGET_DISCUSSION:
            steps.append("Set your budget preferences")
        elif state == ConversationState.FINALIZATION:
            steps.append("Review and finalize your itinerary")
        
        return steps