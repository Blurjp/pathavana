# Hint Generation System Documentation

## Overview
The Pathavana backend now includes a sophisticated hint generation system that provides contextual, actionable hints to help travelers create better travel plans. The system analyzes conversation context, extracts entities, and generates relevant suggestions based on the current state of the travel planning process.

## Architecture

### Core Components

1. **DynamicHintGenerator** (`app/services/hint_generator.py`)
   - Main class responsible for generating contextual hints
   - Tracks conversation state through the `ConversationState` enum
   - Extracts travel entities using pattern recognition
   - Generates hints based on state and extracted entities

2. **EnhancedHintGenerator** (`app/services/travel_hints.py`)
   - Extends DynamicHintGenerator with travel-specific intelligence
   - Includes destination-specific information (Paris, Tokyo, Bali)
   - Provides seasonal advice and budget recommendations
   - Generates activity suggestions based on traveler profile

3. **DatabaseTravelSessionManager** Integration
   - Modified to use EnhancedHintGenerator
   - Passes conversation history to hint generator
   - Includes hints in AI responses

## Features

### Conversation States
- **INITIAL**: First interaction, no context
- **DESTINATION_SELECTION**: User hasn't chosen destination
- **DATE_SELECTION**: Destination chosen, dates needed
- **HOTEL_SEARCH**: Searching for accommodations
- **FLIGHT_SEARCH**: Looking for flights
- **ACTIVITY_PLANNING**: Planning activities and experiences
- **BUDGET_DISCUSSION**: Discussing trip budget
- **FINALIZATION**: Reviewing and finalizing plans
- **COMPLETED**: Trip planning complete

### Entity Extraction
The system can extract:
- **Destinations**: Cities (Paris, Tokyo, etc.) and regions (Patagonia, French Riviera)
- **Dates**: Relative (tomorrow, next week), absolute (specific dates), seasonal (summer)
- **Activities**: Museums, tours, beaches, hiking, etc.
- **Budget preferences**: Budget, mid-range, luxury, or specific amounts

### Hint Types
- **suggestion**: Actionable suggestions for next steps
- **tip**: Helpful tips and best practices
- **info**: Informational content about destinations
- **seasonal**: Season-specific advice
- **budget**: Budget-related recommendations
- **filter**: Search filtering options
- **insider_tip**: Local knowledge and insider tips
- **recommendation**: Specific recommendations
- **checklist**: Pre-trip checklists
- **action**: Direct actions to take

## API Integration

### Create Session Response
```json
POST /api/v1/travel/sessions
{
  "data": {
    "session_id": "...",
    "metadata": {
      "hints": [...],
      "conversation_state": "initial",
      "extracted_entities": [...],
      "next_steps": [...]
    }
  }
}
```

### Chat Response
```json
POST /api/v1/travel/sessions/{id}/chat
{
  "data": {
    "message": "AI response",
    "hints": [...],
    "conversation_state": "hotel_search",
    "extracted_entities": [...],
    "next_steps": [...]
  }
}
```

## Example Usage

### Initial Query
**User**: "I want to plan a romantic trip to Paris in June for our anniversary"

**System Response**:
```json
{
  "hints": [
    {
      "type": "seasonal",
      "text": "Best time to visit Paris: April-June, September-October",
      "action": "show_weather_forecast"
    },
    {
      "type": "budget",
      "text": "Average daily budget in Paris: $150",
      "action": "calculate_trip_cost"
    },
    {
      "type": "insider_tip",
      "text": "Book museum tickets online to skip lines",
      "action": "more_paris_tips"
    }
  ],
  "extracted_entities": [
    {"type": "destination", "value": "Paris", "confidence": 0.9},
    {"type": "date", "value": "june", "confidence": 0.8}
  ],
  "conversation_state": "initial"
}
```

### Hotel Search
**User**: "I need a luxury hotel near the Eiffel Tower with a spa"

**System Response**:
```json
{
  "hints": [
    {
      "type": "filter",
      "text": "Filter by amenities (pool, gym, spa)",
      "action": "apply_hotel_filters"
    },
    {
      "type": "tip",
      "text": "Best neighborhoods in Paris for tourists",
      "action": "show_neighborhood_guide"
    }
  ],
  "conversation_state": "hotel_search",
  "extracted_entities": [
    {"type": "budget", "value": "luxury", "confidence": 0.8}
  ]
}
```

## Testing

Run the hint generation tests:
```bash
# Basic hint test
python test_hints.py

# Detailed hint test
python test_hint_details.py
```

## Extending the System

### Adding New Destinations
Edit `app/services/travel_hints.py` and add to the `destination_info` dictionary:
```python
"New York": {
    "best_season": "April-June, September-November",
    "avg_daily_budget": {"budget": 120, "mid-range": 250, "luxury": 500},
    "must_see": ["Statue of Liberty", "Central Park", "Times Square"],
    "neighborhoods": {...},
    "tips": [...]
}
```

### Adding New Hint Types
1. Add pattern recognition in `DynamicHintGenerator`
2. Add hint generation logic in `generate_hints()`
3. Update API response handling if needed

### Adding New Conversation States
1. Add to `ConversationState` enum
2. Update `analyze_conversation_state()` logic
3. Add state-specific hints in `generate_hints()`

## Performance Considerations
- Hints are generated synchronously during response creation
- Pattern matching is optimized with compiled regex patterns
- Hint count is limited to prevent overwhelming users (max 5 by default)
- Entity extraction confidence scores help prioritize relevant hints

## Future Enhancements
1. Machine learning-based entity extraction
2. User preference learning over time
3. Integration with external APIs for real-time data
4. Multi-language support for international travelers
5. Personalized hint ranking based on user behavior