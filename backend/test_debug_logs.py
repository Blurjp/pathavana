"""
Demonstrate the debug logging for AI agent conversation flow.
This script shows how the AI agent processes messages and engages with users.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging to show DEBUG level messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

async def test_debug_flow():
    """Test the conversation flow with debug logging enabled."""
    print("\n" + "="*80)
    print("AI AGENT DEBUG LOG DEMONSTRATION")
    print("="*80)
    print("This test shows the complete flow of how the AI agent processes messages.")
    print("Watch the debug logs to see each step of the conversation processing.")
    print("="*80 + "\n")
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    from app.services.travel_session_db import DatabaseTravelSessionManager
    from app.schemas.travel import TravelSessionCreate, ChatRequest
    from app.core.logger import logger
    
    # Create test database
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test_debug.db",
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Test conversation
    async with async_session() as db:
        travel_service = DatabaseTravelSessionManager(db)
        
        print("\n📝 SCENARIO: Planning a trip to Paris")
        print("-" * 60)
        
        # Try to initialize orchestrator
        orchestrator = None
        try:
            from app.agents.unified_orchestrator import UnifiedOrchestrator
            print("\n🔄 Attempting to initialize AI Orchestrator...")
            orchestrator = UnifiedOrchestrator(travel_service)
            print("✅ AI Orchestrator available - will use LLM responses\n")
        except Exception as e:
            print(f"⚠️  AI Orchestrator not available: {e}")
            print("   Will use template-based responses\n")
        
        # Create a session
        print("1️⃣  Creating new travel session...")
        session = await travel_service.create_session(
            user=None,
            request=TravelSessionCreate(
                message="I want to plan a trip to Paris",
                metadata={"source": "debug_test"}
            )
        )
        print(f"   Session created: {session.session_id}\n")
        
        # Test messages
        test_messages = [
            "I want to go next weekend",
            "It's just me traveling alone", 
            "What are the best places to visit?"
        ]
        
        for i, message in enumerate(test_messages, 2):
            print(f"\n{i}️⃣  Processing message: '{message}'")
            print("-" * 60)
            
            # Send message
            result = await travel_service.add_chat_message(
                session_id=str(session.session_id),
                request=ChatRequest(message=message),
                orchestrator=orchestrator
            )
            
            if result:
                ai_response = result['ai_response']
                print(f"\n   AI Response: {ai_response['content']}")
                
                # Show additional debug info
                if 'metadata' in ai_response:
                    metadata = ai_response['metadata']
                    if metadata.get('updated_context'):
                        print(f"   Context Update: {metadata['updated_context']}")
                    if metadata.get('tools_used'):
                        print(f"   Tools Used: {metadata['tools_used']}")
                    if metadata.get('hints'):
                        print(f"   Hints Generated: {len(metadata['hints'])} hints")
            
            # Small delay to make logs easier to read
            await asyncio.sleep(0.5)
    
    # Cleanup
    await engine.dispose()
    
    # Remove test database
    import os
    if os.path.exists("test_debug.db"):
        os.remove("test_debug.db")
    
    print("\n" + "="*80)
    print("DEBUG LOG ANALYSIS")
    print("="*80)
    print("\nThe debug logs show:")
    print("1. Orchestrator initialization (checking LLM credentials)")
    print("2. Message processing flow through the API")
    print("3. Context extraction from user messages")
    print("4. AI response generation (orchestrator vs template)")
    print("5. Hint generation and metadata updates")
    print("\nKey log markers to look for:")
    print("🤖 - Orchestrator operations")
    print("🔄 - Message processing")
    print("🎨 - Response generation")
    print("✅ - Successful operations")
    print("❌ - Errors and fallbacks")
    print("="*80 + "\n")

if __name__ == "__main__":
    print("Starting AI Agent Debug Log Test...")
    print("Note: Set LOG_LEVEL=DEBUG in your environment for full details")
    asyncio.run(test_debug_flow())