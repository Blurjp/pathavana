#!/usr/bin/env python3
"""
Test script to verify trip plan intent detection works correctly.
"""

import sys
import asyncio
from app.services.trip_context_service import TripContextService

def test_trip_plan_intent_detection():
    """Test various messages to see if trip plan intent is detected correctly."""
    
    service = TripContextService()
    
    test_messages = [
        "Plan a trip to Paris",
        "Create a trip plan for Tokyo next month",
        "I want to plan my vacation to London",
        "Help me plan a weekend trip to New York",
        "Make a trip plan for Bali",
        "I'd like to visit Paris in March", # Should NOT create trip plan (no planning intent)
        "What's the weather like in Tokyo?", # Should NOT create trip plan
        "Plan my trip to Rome for 5 days"
    ]
    
    print("🧪 Testing Trip Plan Intent Detection")
    print("=" * 50)
    
    for message in test_messages:
        result = service.detect_trip_plan_intent(message, context={})
        
        status = "✅ CREATES TRIP PLAN" if result["wants_trip_plan"] else "❌ NO TRIP PLAN"
        confidence = result["confidence"]
        reason = result["reason"]
        
        print(f"\n📝 Message: '{message}'")
        print(f"   {status} (confidence: {confidence:.2f})")
        print(f"   Reason: {reason}")
        
        if result["trip_info"]:
            print(f"   Trip Info: {result['trip_info']}")

if __name__ == "__main__":
    test_trip_plan_intent_detection()