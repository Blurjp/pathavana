#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.travel_session_db import DatabaseTravelSessionManager
from app.core.logger import logger

async def test_session_persistence():
    """Test if sessions persist across different database connections."""
    print("Testing session persistence...")
    
    session_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # First, create a session via HTTP
    base_url = "http://localhost:8001/api/v1/travel"
    
    async with aiohttp.ClientSession() as http_session:
        create_data = {
            "message": "I want to plan a trip to Paris",
            "source": "web"
        }
        
        print("1. Creating travel session via HTTP...")
        async with http_session.post(f"{base_url}/sessions", json=create_data) as resp:
            if resp.status == 201:
                result = await resp.json()
                session_id = result["data"]["session_id"]
                print(f"   ✅ HTTP Session created: {session_id}")
            else:
                text = await resp.text()
                print(f"   ❌ Failed to create session: {resp.status} - {text}")
                return
    
    # Now check if the session exists via direct database access
    print("2. Checking session via direct database access...")
    db = get_db()
    async for db_session in db:
        session_manager = DatabaseTravelSessionManager(db_session)
        
        # Try to get the session
        session_data = await session_manager.get_session(session_id)
        
        if session_data:
            print(f"   ✅ Session found via direct DB access")
            print(f"   Session data keys: {list(session_data.keys())}")
        else:
            print(f"   ❌ Session NOT found via direct DB access")
        
        # Try to get the session object
        session_obj = await session_manager._get_session_object(session_id)
        
        if session_obj:
            print(f"   ✅ Session object found via direct DB access")
            print(f"   Session object ID: {session_obj.session_id}")
        else:
            print(f"   ❌ Session object NOT found via direct DB access")
        
        break
    
    # Now test adding a chat message via direct DB
    print("3. Testing chat via direct database access...")
    db = get_db()
    async for db_session in db:
        session_manager = DatabaseTravelSessionManager(db_session)
        
        from app.schemas.travel import ChatRequest
        chat_request = ChatRequest(
            message="Hello, I want to plan a trip",
            metadata={}
        )
        
        result = await session_manager.add_chat_message(
            session_id=session_id,
            request=chat_request,
            user_id=None,
            orchestrator=None
        )
        
        if result:
            print(f"   ✅ Chat via direct DB access successful")
        else:
            print(f"   ❌ Chat via direct DB access failed")
        
        break

if __name__ == "__main__":
    asyncio.run(test_session_persistence())