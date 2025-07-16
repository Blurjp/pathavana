"""
Enhanced travel hint generation with destination-specific recommendations.

This module provides advanced hint generation capabilities including:
- Destination-specific tips and recommendations
- Seasonal travel advice
- Budget optimization hints
- Activity recommendations based on traveler profile
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from .hint_generator import DynamicHintGenerator, ConversationState, TravelEntity


class TravelHintEnhancer:
    """Enhances basic hints with travel-specific intelligence."""
    
    def __init__(self):
        self.destination_info = {
            "Paris": {
                "best_season": "April-June, September-October",
                "avg_daily_budget": {"budget": 80, "mid-range": 150, "luxury": 300},
                "must_see": ["Eiffel Tower", "Louvre Museum", "Arc de Triomphe"],
                "neighborhoods": {
                    "romantic": "Montmartre, Le Marais",
                    "shopping": "Champs-Élysées, Le Marais",
                    "nightlife": "Oberkampf, Bastille"
                },
                "tips": [
                    "Book museum tickets online to skip lines",
                    "Metro day pass is cost-effective for sightseeing",
                    "Many museums are free on first Sunday of month"
                ]
            },
            "Tokyo": {
                "best_season": "March-May (Cherry Blossoms), October-November",
                "avg_daily_budget": {"budget": 100, "mid-range": 200, "luxury": 400},
                "must_see": ["Senso-ji Temple", "Tokyo Skytree", "Shibuya Crossing"],
                "neighborhoods": {
                    "traditional": "Asakusa, Ueno",
                    "modern": "Shibuya, Shinjuku",
                    "upscale": "Ginza, Roppongi"
                },
                "tips": [
                    "Get a JR Pass for unlimited train travel",
                    "Download Google Translate offline for Japanese",
                    "Cash is king - many places don't accept cards"
                ]
            },
            "Bali": {
                "best_season": "April-October (Dry Season)",
                "avg_daily_budget": {"budget": 50, "mid-range": 100, "luxury": 250},
                "must_see": ["Tanah Lot Temple", "Ubud Rice Terraces", "Uluwatu Temple"],
                "neighborhoods": {
                    "beach": "Seminyak, Canggu",
                    "culture": "Ubud",
                    "quiet": "Amed, Lovina"
                },
                "tips": [
                    "Rent a scooter for easy exploration",
                    "Respect temple dress codes",
                    "Bargain at markets - start at 30% of asking price"
                ]
            }
        }
        
        self.activity_recommendations = {
            "adventure": [
                "Hiking and trekking",
                "Water sports and diving",
                "Rock climbing",
                "Zip-lining"
            ],
            "cultural": [
                "Museum tours",
                "Historical sites",
                "Local cooking classes",
                "Traditional performances"
            ],
            "relaxation": [
                "Spa treatments",
                "Beach lounging",
                "Yoga retreats",
                "Scenic cafes"
            ],
            "family": [
                "Theme parks",
                "Interactive museums",
                "Zoo and aquariums",
                "Beach activities"
            ]
        }
    
    def enhance_hints_with_destination_info(self, 
                                           hints: List[Dict[str, str]], 
                                           destination: Optional[str],
                                           context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Enhance hints with destination-specific information."""
        enhanced_hints = hints.copy()
        
        if destination and destination in self.destination_info:
            dest_info = self.destination_info[destination]
            
            # Add seasonal advice
            enhanced_hints.append({
                "type": "seasonal",
                "text": f"Best time to visit {destination}: {dest_info['best_season']}",
                "action": "show_weather_forecast"
            })
            
            # Add budget information
            budget_pref = context.get('budget', 'mid-range')
            if budget_pref in dest_info['avg_daily_budget']:
                daily_budget = dest_info['avg_daily_budget'][budget_pref]
                enhanced_hints.append({
                    "type": "budget",
                    "text": f"Average daily budget in {destination}: ${daily_budget}",
                    "action": "calculate_trip_cost"
                })
            
            # Add a destination-specific tip
            if dest_info['tips']:
                enhanced_hints.append({
                    "type": "insider_tip",
                    "text": dest_info['tips'][0],
                    "action": f"more_{destination.lower()}_tips"
                })
        
        return enhanced_hints
    
    def generate_activity_hints(self, 
                               traveler_profile: str,
                               destination: Optional[str]) -> List[Dict[str, str]]:
        """Generate activity hints based on traveler profile."""
        hints = []
        
        if traveler_profile in self.activity_recommendations:
            activities = self.activity_recommendations[traveler_profile]
            for activity in activities[:2]:
                hints.append({
                    "type": "activity",
                    "text": f"Recommended: {activity}",
                    "action": f"find_{activity.lower().replace(' ', '_')}"
                })
        
        return hints
    
    def generate_smart_suggestions(self,
                                  state: ConversationState,
                                  context: Dict[str, Any],
                                  recent_searches: List[str]) -> List[Dict[str, str]]:
        """Generate intelligent suggestions based on user behavior."""
        suggestions = []
        
        # If user searched for flights but not hotels
        if 'flights' in recent_searches and 'hotels' not in recent_searches:
            suggestions.append({
                "type": "next_action",
                "text": "Now let's find the perfect hotel",
                "action": "search_hotels"
            })
        
        # If dates are approaching, suggest urgent booking
        if context.get('dates'):
            # Simple date parsing for demonstration
            days_until_trip = 30  # Would calculate from actual dates
            if days_until_trip < 14:
                suggestions.append({
                    "type": "urgent",
                    "text": "Book soon! Prices typically increase close to travel dates",
                    "action": "show_price_alerts"
                })
        
        # If multiple destinations mentioned, suggest comparison
        if context.get('alternative_destinations'):
            suggestions.append({
                "type": "comparison",
                "text": "Compare destinations side-by-side",
                "action": "compare_destinations"
            })
        
        return suggestions


class EnhancedHintGenerator(DynamicHintGenerator):
    """Enhanced hint generator with travel-specific features."""
    
    def __init__(self):
        super().__init__()
        self.enhancer = TravelHintEnhancer()
    
    def generate_hints(self, 
                      message: str,
                      conversation_state: ConversationState,
                      current_context: Dict,
                      entities: List[TravelEntity]) -> List[Dict[str, str]]:
        """Generate enhanced hints with destination-specific information."""
        # Get base hints
        base_hints = super().generate_hints(message, conversation_state, current_context, entities)
        
        # Extract destination from context or entities
        destination = current_context.get('destination')
        if not destination:
            destination_entity = next((e for e in entities if e.type == 'destination'), None)
            if destination_entity:
                destination = destination_entity.value
        
        # Enhance hints with destination info
        enhanced_hints = self.enhancer.enhance_hints_with_destination_info(
            base_hints, destination, current_context
        )
        
        # Add activity hints based on implied traveler profile
        traveler_profile = self._infer_traveler_profile(message, current_context)
        if traveler_profile:
            activity_hints = self.enhancer.generate_activity_hints(traveler_profile, destination)
            enhanced_hints.extend(activity_hints)
        
        # Add smart suggestions based on context
        recent_searches = current_context.get('recent_searches', [])
        smart_suggestions = self.enhancer.generate_smart_suggestions(
            conversation_state, current_context, recent_searches
        )
        enhanced_hints.extend(smart_suggestions)
        
        # Remove duplicates and limit
        seen_actions = set()
        unique_hints = []
        for hint in enhanced_hints:
            if hint['action'] not in seen_actions:
                seen_actions.add(hint['action'])
                unique_hints.append(hint)
        
        return unique_hints[:5]  # Limit to 5 hints
    
    def _infer_traveler_profile(self, message: str, context: Dict) -> Optional[str]:
        """Infer traveler profile from message and context."""
        message_lower = message.lower()
        
        adventure_keywords = ['adventure', 'hiking', 'extreme', 'sports', 'diving']
        cultural_keywords = ['history', 'museum', 'culture', 'art', 'heritage']
        relaxation_keywords = ['relax', 'spa', 'beach', 'peaceful', 'quiet']
        family_keywords = ['family', 'kids', 'children', 'child-friendly']
        
        if any(keyword in message_lower for keyword in adventure_keywords):
            return 'adventure'
        elif any(keyword in message_lower for keyword in cultural_keywords):
            return 'cultural'
        elif any(keyword in message_lower for keyword in relaxation_keywords):
            return 'relaxation'
        elif any(keyword in message_lower for keyword in family_keywords):
            return 'family'
        
        # Check context for traveler count
        travelers = context.get('travelers')
        if travelers and isinstance(travelers, (int, float)) and travelers >= 3:
            return 'family'
        
        return None