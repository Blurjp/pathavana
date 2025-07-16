"""
Test the AI orchestrator integration with the travel session manager.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup test environment variables for template responses
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_pathavana.db"

async def test_orchestrator_integration():
    """Test the orchestrator integration with different scenarios."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models import Base  # Import Base from __init__ to get all models registered
    from app.models.unified_travel_session import UnifiedTravelSession
    from app.models.user import User
    from app.services.travel_session_db import DatabaseTravelSessionManager
    from app.schemas.travel import TravelSessionCreate, ChatRequest
    from app.core.logger import logger
    
    # Create test database
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
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
    
    # Test scenarios
    test_cases = [
        {
            "name": "Weekend trip to Paris",
            "messages": [
                "Plan a weekend trip to Paris",
                "I want to go next weekend",
                "Just me traveling alone",
                "Find me some interesting places to visit"
            ]
        },
        {
            "name": "Family vacation",
            "messages": [
                "I need help planning a family vacation",
                "We want to go to Tokyo",
                "4 people - 2 adults and 2 kids",
                "What activities are good for families?"
            ]
        },
        {
            "name": "Business trip",
            "messages": [
                "I have a business trip to London",
                "Need a hotel near the financial district",
                "Flying in next Monday, leaving Wednesday",
                "What's the best way to get from Heathrow to the city?"
            ]
        }
    ]
    
    # Test with orchestrator (will fail if LLM not configured)
    print("\n" + "="*60)
    print("Testing WITH Orchestrator (requires LLM configuration)")
    print("="*60)
    
    try:
        from app.agents.unified_orchestrator import UnifiedOrchestrator
        
        async with async_session() as db:
            travel_service = DatabaseTravelSessionManager(db)
            
            # Try to create orchestrator
            try:
                orchestrator = UnifiedOrchestrator(travel_service)
                print("✅ Orchestrator initialized successfully!")
                
                # Test a conversation
                test_case = test_cases[0]
                print(f"\nTesting: {test_case['name']}")
                
                # Create a session
                session = await travel_service.create_session(
                    user=None,
                    request=TravelSessionCreate(
                        message=test_case['messages'][0],
                        metadata={"test": True}
                    )
                )
                
                print(f"Session created: {session.session_id}")
                
                # Send messages
                for i, message in enumerate(test_case['messages'][1:], 1):
                    print(f"\n👤 User: {message}")
                    
                    result = await travel_service.add_chat_message(
                        session_id=str(session.session_id),
                        request=ChatRequest(message=message),
                        orchestrator=orchestrator
                    )
                    
                    if result:
                        ai_response = result['ai_response']
                        print(f"🤖 AI: {ai_response['content']}")
                        
                        # Show metadata if available
                        metadata = ai_response.get('metadata', {})
                        if metadata.get('tools_used'):
                            print(f"   Tools used: {metadata['tools_used']}")
                        if metadata.get('clarifying_questions'):
                            print(f"   Questions: {metadata['clarifying_questions']}")
                
            except Exception as e:
                print(f"❌ Orchestrator initialization failed: {e}")
                print("   This is expected if LLM credentials are not configured.")
                
    except ImportError as e:
        print(f"❌ Could not import orchestrator: {e}")
    
    # Test without orchestrator (template responses)
    print("\n" + "="*60)
    print("Testing WITHOUT Orchestrator (template responses)")
    print("="*60)
    
    async with async_session() as db:
        travel_service = DatabaseTravelSessionManager(db)
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            
            # Create a session
            session = await travel_service.create_session(
                user=None,
                request=TravelSessionCreate(
                    message=test_case['messages'][0],
                    metadata={"test": True}
                )
            )
            
            print(f"Session created: {session.session_id}")
            
            # Send messages without orchestrator
            for i, message in enumerate(test_case['messages'], 1):
                print(f"\n👤 User: {message}")
                
                result = await travel_service.add_chat_message(
                    session_id=str(session.session_id),
                    request=ChatRequest(message=message),
                    orchestrator=None  # No orchestrator - will use templates
                )
                
                if result:
                    ai_response = result['ai_response']
                    print(f"🤖 AI: {ai_response['content']}")
                    
                    # Check if response is repetitive
                    if i > 1 and ai_response['content'].startswith("I understand."):
                        print("   ⚠️  WARNING: Repetitive response detected!")
    
    # Cleanup
    await engine.dispose()
    
    # Remove test database
    if os.path.exists("test_pathavana.db"):
        os.remove("test_pathavana.db")

if __name__ == "__main__":
    print("AI Orchestrator Integration Test")
    print("================================")
    print("\nThis test will:")
    print("1. Try to use the AI orchestrator (requires LLM credentials)")
    print("2. Fall back to template responses if orchestrator fails")
    print("3. Show the difference in conversation quality")
    
    asyncio.run(test_orchestrator_integration())