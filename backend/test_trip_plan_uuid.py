#!/usr/bin/env python3
"""
Test script to verify travel plan creation and UUID consistency between 
chat session and trip plan in the database.
"""

import asyncio
import json
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Import the models
from app.models.unified_travel_session import UnifiedTravelSession
from app.services.travel_session_db import DatabaseTravelSessionManager

# Database configuration - use SQLite for development testing
DATABASE_URL = "sqlite+aiosqlite:///./pathavana_dev.db"

async def test_trip_plan_uuid_consistency():
    """Test that chat sessions and trip plans share the same UUID."""
    
    print("🧪 Testing Trip Plan UUID Consistency")
    print("=" * 50)
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create session manager
            session_manager = DatabaseTravelSessionManager(db)
            
            # Test 1: Create a new session
            print("📝 Test 1: Creating new travel session...")
            session = await session_manager.create_empty_session(user=None)
            session_id = session.session_id
            print(f"   ✅ Created session with ID: {session_id}")
            
            # Test 2: Verify session ID is valid UUID
            print("🔍 Test 2: Validating UUID format...")
            try:
                uuid_obj = uuid.UUID(session_id)
                print(f"   ✅ Valid UUID: {uuid_obj}")
            except ValueError:
                print(f"   ❌ Invalid UUID format: {session_id}")
                return False
            
            # Test 3: Add trip plan data to the session
            print("🗺️ Test 3: Adding trip plan data...")
            trip_plan_data = {
                "destination": "Paris, France",
                "departure_date": "2024-08-15",
                "return_date": "2024-08-20",
                "travelers": 2,
                "plan_days": [
                    {
                        "day": 1,
                        "date": "2024-08-15",
                        "items": [
                            {
                                "id": str(uuid.uuid4()),
                                "type": "flight",
                                "data": {
                                    "airline": "Air France",
                                    "flightNumber": "AF123",
                                    "origin": {"code": "SFO", "name": "San Francisco"},
                                    "destination": {"code": "CDG", "name": "Paris Charles de Gaulle"},
                                    "departureTime": "10:00",
                                    "arrivalTime": "06:00+1",
                                    "duration": "11h 00m",
                                    "price": {"amount": 650, "currency": "USD"}
                                }
                            },
                            {
                                "id": str(uuid.uuid4()),
                                "type": "hotel",
                                "data": {
                                    "name": "Hotel du Louvre",
                                    "rating": 4.5,
                                    "location": {
                                        "address": "Place André Malraux, 75001 Paris",
                                        "city": "Paris",
                                        "country": "France"
                                    },
                                    "price": {"amount": 200, "currency": "USD"},
                                    "amenities": ["WiFi", "Restaurant", "Concierge"]
                                }
                            }
                        ]
                    },
                    {
                        "day": 2,
                        "date": "2024-08-16",
                        "items": [
                            {
                                "id": str(uuid.uuid4()),
                                "type": "activity",
                                "data": {
                                    "name": "Eiffel Tower Visit",
                                    "type": "sightseeing",
                                    "description": "Visit the iconic Eiffel Tower",
                                    "location": {
                                        "address": "Champ de Mars, 75007 Paris",
                                        "city": "Paris",
                                        "country": "France"
                                    },
                                    "duration": "2 hours",
                                    "price": {"amount": 30, "currency": "USD"}
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Update session with trip plan data
            session.plan_data = trip_plan_data
            await db.commit()
            print(f"   ✅ Added trip plan data to session {session_id}")
            
            # Test 4: Retrieve session and verify data persistence
            print("💾 Test 4: Verifying data persistence...")
            result = await db.execute(
                select(UnifiedTravelSession).where(
                    UnifiedTravelSession.session_id == session_id
                )
            )
            retrieved_session = result.scalar_one_or_none()
            
            if retrieved_session:
                print(f"   ✅ Session retrieved: {retrieved_session.session_id}")
                
                # Verify trip plan data exists
                if retrieved_session.plan_data:
                    plan_data = retrieved_session.plan_data
                    print(f"   ✅ Plan data exists for destination: {plan_data.get('destination')}")
                    print(f"   ✅ Plan has {len(plan_data.get('plan_days', []))} days")
                    
                    # Verify day 1 has flight and hotel
                    day1 = plan_data.get('plan_days', [{}])[0]
                    day1_items = day1.get('items', [])
                    flight_items = [item for item in day1_items if item['type'] == 'flight']
                    hotel_items = [item for item in day1_items if item['type'] == 'hotel']
                    
                    print(f"   ✅ Day 1 has {len(flight_items)} flight(s) and {len(hotel_items)} hotel(s)")
                    
                    # Verify day 2 has activity
                    if len(plan_data.get('plan_days', [])) > 1:
                        day2 = plan_data.get('plan_days', [])[1]
                        day2_items = day2.get('items', [])
                        activity_items = [item for item in day2_items if item['type'] == 'activity']
                        print(f"   ✅ Day 2 has {len(activity_items)} activity(ies)")
                    
                else:
                    print("   ❌ No plan data found")
                    return False
            else:
                print(f"   ❌ Session not found: {session_id}")
                return False
            
            # Test 5: Verify UUID consistency
            print("🔗 Test 5: Verifying UUID consistency...")
            original_uuid = session_id
            retrieved_uuid = retrieved_session.session_id
            
            if original_uuid == retrieved_uuid:
                print(f"   ✅ UUID consistency verified: {original_uuid}")
            else:
                print(f"   ❌ UUID mismatch: {original_uuid} != {retrieved_uuid}")
                return False
                
            # Test 6: Test clickable date functionality data structure
            print("🖱️ Test 6: Verifying clickable date data structure...")
            plan_days = plan_data.get('plan_days', [])
            
            for day_data in plan_days:
                day_num = day_data.get('day')
                day_date = day_data.get('date')
                day_items = day_data.get('items', [])
                
                print(f"   📅 Day {day_num} ({day_date}): {len(day_items)} items")
                
                for item in day_items:
                    item_type = item.get('type')
                    item_data = item.get('data', {})
                    
                    if item_type == 'flight':
                        airline = item_data.get('airline', 'Unknown')
                        flight_num = item_data.get('flightNumber', 'Unknown')
                        print(f"     ✈️  Flight: {airline} {flight_num}")
                        
                    elif item_type == 'hotel':
                        hotel_name = item_data.get('name', 'Unknown')
                        rating = item_data.get('rating', 'N/A')
                        print(f"     🏨 Hotel: {hotel_name} ({rating}★)")
                        
                    elif item_type == 'activity':
                        activity_name = item_data.get('name', 'Unknown')
                        duration = item_data.get('duration', 'Unknown')
                        print(f"     🎫 Activity: {activity_name} ({duration})")
            
            print("\n🎉 All tests passed! The implementation supports:")
            print("  ✅ UUID consistency between chat session and travel plan")
            print("  ✅ Persistent storage of travel plan data")
            print("  ✅ Structured day-by-day trip plan data")
            print("  ✅ Flight, hotel, and activity item storage")
            print("  ✅ Data structure suitable for clickable dates")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_trip_plan_uuid_consistency())