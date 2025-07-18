#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.travel_session_db import DatabaseTravelSessionManager
from app.schemas.travel import ChatRequest, TravelSessionCreate
from app.core.logger import logger

async def test_chat_functionality():
    """Test chat functionality to debug the failing test."""
    logger.info("Testing chat functionality...")
    
    # Use the get_db dependency
    db = get_db()
    async for db_session in db:
        # Create a session manager
        session_manager = DatabaseTravelSessionManager(db_session)
        
        # Test creating a session
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        logger.info(f"Creating session {session_id}")
        
        try:
            # Create session with initial message
            session = await session_manager.get_or_create_session(
                session_id=session_id,
                user=None,
                initial_message="I want to plan a trip to Paris"
            )
            
            if session:
                logger.info(f"Session created: {session.session_id}")
                
                # Test adding a chat message
                chat_request = ChatRequest(
                    message="Hello, I want to plan a trip",
                    metadata={}
                )
                
                logger.info(f"Testing chat message: {chat_request.message}")
                result = await session_manager.add_chat_message(
                    session_id=session_id,
                    request=chat_request,
                    user_id=None,
                    orchestrator=None  # No orchestrator for testing
                )
                
                if result:
                    logger.info("Chat message processed successfully!")
                    logger.info(f"AI response: {result['ai_response']['content'][:100]}...")
                else:
                    logger.error("Chat message processing failed")
                
            else:
                logger.error("Failed to create session")
                
        except Exception as e:
            logger.error(f"Error testing chat functionality: {e}", exc_info=True)
        
        # Exit after first iteration
        break

if __name__ == "__main__":
    asyncio.run(test_chat_functionality())