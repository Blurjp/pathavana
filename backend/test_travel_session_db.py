#!/usr/bin/env python3
"""
Test script for database-backed travel session implementation.
"""
import asyncio
import uuid
from app.core.database import get_db_context
# Import all models to ensure they're registered with SQLAlchemy
from app.models import User, UnifiedTravelSession
from app.services.travel_session_db import DatabaseTravelSessionManager
from app.schemas.travel import TravelSessionCreate, ChatRequest

async def test_travel_sessions():
    """Test travel session operations."""
    print("Testing Database Travel Session Implementation")
    print("=" * 50)
    
    async with get_db_context() as db:
        manager = DatabaseTravelSessionManager(db)
        
        # Test 1: Create a new session
        print("\n1. Creating new travel session...")
        create_request = TravelSessionCreate(
            message="I want to plan a trip to Tokyo next month",
            source="test",
            metadata={"test": True}
        )
        
        session = await manager.create_session(
            user=None,  # Anonymous user
            request=create_request
        )
        
        print(f"✓ Created session: {session.session_id}")
        print(f"  Status: {session.status}")
        print(f"  Context: {session.session_data.get('parsed_intent', {})}")
        
        # Test 2: Retrieve the session
        print("\n2. Retrieving session...")
        retrieved = await manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        print(f"✓ Retrieved session successfully")
        
        # Test 3: Add a chat message
        print("\n3. Adding chat message...")
        chat_request = ChatRequest(
            message="I prefer business class flights",
            metadata={"preference": True}
        )
        
        result = await manager.add_chat_message(
            session_id=session.session_id,
            request=chat_request
        )
        
        assert result is not None
        print(f"✓ Added chat message")
        print(f"  AI Response: {result['ai_response']['content'][:100]}...")
        
        # Test 4: Test session recovery (simulate lost session)
        print("\n4. Testing session recovery...")
        fake_session_id = str(uuid.uuid4())
        recovered = await manager.get_or_create_session(
            session_id=fake_session_id,
            user=None,
            initial_message="Recovered session"
        )
        
        assert recovered is not None
        print(f"✓ Successfully created recovery session: {recovered.session_id}")
        
        # Test 5: Verify session persistence
        print("\n5. Verifying persistence...")
        # Create another manager instance (simulating server restart)
        manager2 = DatabaseTravelSessionManager(db)
        persisted = await manager2.get_session(session.session_id)
        
        assert persisted is not None
        conversation_count = len(persisted.session_data.get("conversation_history", []))
        assert conversation_count >= 3  # Should have at least 3 messages
        print(f"✓ Session persisted correctly with {conversation_count} messages")
        
        print("\n✅ All tests passed! Database persistence is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_travel_sessions())