#!/usr/bin/env python3
"""
Simple test to check trip plan intent detection patterns.
"""

def test_intent_patterns():
    """Test the basic pattern matching for trip plan intent."""
    
    # These are the exact patterns from the TripContextService
    trip_plan_phrases = [
        "create a trip plan",
        "create my trip plan", 
        "make a trip plan",
        "build a trip plan",
        "start planning my trip",
        "plan my trip",
        "plan a trip",
        "create an itinerary",
        "build my itinerary",
        "organize my trip",
        "put together my trip",
        "let's plan",
        "help me plan",
        "i want to plan",
        "create a travel plan",
        "save my trip",
        "add to my trip plan",
        "add this to my trip"
    ]
    
    test_messages = [
        "Plan a trip to Paris",
        "Create a trip plan for Tokyo next month", 
        "I want to plan my vacation to London",
        "Help me plan a weekend trip to New York",
        "Make a trip plan for Bali",
        "Plan my trip to Rome for 5 days",
        "I'd like to visit Paris in March",  # Should NOT match
        "What's the weather like in Tokyo?", # Should NOT match
    ]
    
    print("🧪 Testing Trip Plan Intent Pattern Matching")
    print("=" * 60)
    
    for message in test_messages:
        message_lower = message.lower()
        matches = []
        
        # Check for matches
        for phrase in trip_plan_phrases:
            if phrase in message_lower:
                matches.append(phrase)
        
        status = "✅ CREATES TRIP PLAN" if matches else "❌ NO TRIP PLAN"
        print(f"\n📝 Message: '{message}'")
        print(f"   {status}")
        if matches:
            print(f"   Matched phrases: {matches}")

if __name__ == "__main__":
    test_intent_patterns()