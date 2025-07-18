#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database_config import DatabaseConfig
from app.core.database import get_db
from app.services.travel_session_db import DatabaseTravelSessionManager
from app.core.logger import logger

async def test_session_retrieval():
    """Test session retrieval to debug greenlet issue."""
    logger.info("Testing session retrieval...")
    
    # Use the get_db dependency
    db = get_db()
    async for db_session in db:
        # Create a session manager
        session_manager = DatabaseTravelSessionManager(db_session)
        
        # Test retrieving a session
        session_id = "1347fd5a-1063-4bc9-93b0-b9b08ee1abb6"
        logger.info(f"Attempting to retrieve session {session_id}")
        
        try:
            session = await session_manager.get_session(session_id)
            
            if session:
                logger.info(f"Session found: {session.session_id}")
                logger.info(f"Session status: {session.status}")
                logger.info(f"Session user_id: {session.user_id}")
                
                # Test accessing JSONB fields
                logger.info("Testing JSONB field access...")
                
                try:
                    session_data = session.session_data
                    logger.info(f"session_data type: {type(session_data)}")
                    logger.info(f"session_data keys: {list(session_data.keys()) if session_data else 'None'}")
                except Exception as e:
                    logger.error(f"Error accessing session_data: {e}")
                
                try:
                    plan_data = session.plan_data
                    logger.info(f"plan_data type: {type(plan_data)}")
                    logger.info(f"plan_data keys: {list(plan_data.keys()) if plan_data else 'None'}")
                except Exception as e:
                    logger.error(f"Error accessing plan_data: {e}")
                
                try:
                    session_metadata = session.session_metadata
                    logger.info(f"session_metadata type: {type(session_metadata)}")
                    logger.info(f"session_metadata keys: {list(session_metadata.keys()) if session_metadata else 'None'}")
                except Exception as e:
                    logger.error(f"Error accessing session_metadata: {e}")
                
            else:
                logger.warning(f"Session {session_id} not found")
                
        except Exception as e:
            logger.error(f"Error retrieving session: {e}", exc_info=True)
        
        # Exit after first iteration
        break

if __name__ == "__main__":
    asyncio.run(test_session_retrieval())