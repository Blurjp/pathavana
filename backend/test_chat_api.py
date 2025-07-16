"""
Test the chat API to verify AI responses are working properly.
"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any

# API configuration
API_BASE_URL = "http://localhost:8001/api/v1"
API_HEADERS = {"Content-Type": "application/json"}

async def create_session(message: str) -> Dict[str, Any]:
    """Create a new travel session."""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/travel/sessions"
        data = {
            "message": message,
            "metadata": {"source": "test"}
        }
        
        async with session.post(url, json=data, headers=API_HEADERS) as response:
            result = await response.json()
            if response.status == 201:
                print(f"✅ Session created: {result['data']['session_id']}")
                return result['data']
            else:
                print(f"❌ Failed to create session: {response.status}")
                print(f"   Error: {result}")
                return None

async def send_chat_message(session_id: str, message: str) -> Dict[str, Any]:
    """Send a chat message to an existing session."""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/travel/sessions/{session_id}/chat"
        data = {
            "message": message,
            "metadata": {}
        }
        
        async with session.post(url, json=data, headers=API_HEADERS) as response:
            result = await response.json()
            if response.status == 200:
                return result['data']
            else:
                print(f"❌ Failed to send message: {response.status}")
                print(f"   Error: {result}")
                return None

async def test_conversation():
    """Test a full conversation flow."""
    print("\n" + "="*60)
    print("Testing AI Chat Conversation")
    print("="*60)
    
    # Test cases for conversation
    conversations = [
        {
            "name": "Weekend Trip to Paris",
            "messages": [
                "Plan a weekend trip to Paris",
                "I want to go next weekend",
                "Just me traveling alone",
                "Find me some interesting places to visit"
            ]
        },
        {
            "name": "Family Vacation",
            "messages": [
                "I need help planning a family vacation to Tokyo",
                "We are 4 people - 2 adults and 2 kids",
                "We want to go in summer",
                "What activities are good for families?"
            ]
        }
    ]
    
    for conv in conversations:
        print(f"\n### Testing: {conv['name']}")
        print("-" * 50)
        
        # Create session with first message
        print(f"\n👤 User: {conv['messages'][0]}")
        session_data = await create_session(conv['messages'][0])
        
        if not session_data:
            print("Failed to create session, skipping...")
            continue
        
        session_id = session_data['session_id']
        
        # Show initial response
        initial_response = session_data.get('initial_response', 'No response')
        print(f"🤖 AI: {initial_response}")
        
        # Check for hints
        if 'metadata' in session_data and 'hints' in session_data['metadata']:
            hints = session_data['metadata']['hints']
            if hints:
                print(f"   💡 Hints: {hints}")
        
        # Send follow-up messages
        for message in conv['messages'][1:]:
            print(f"\n👤 User: {message}")
            
            response_data = await send_chat_message(session_id, message)
            if response_data:
                ai_message = response_data.get('message', 'No response')
                print(f"🤖 AI: {ai_message}")
                
                # Check if response is repetitive
                if ai_message.startswith("I understand.") and len(ai_message) < 50:
                    print("   ⚠️  WARNING: Possible repetitive response detected!")
                
                # Show additional metadata
                if 'hints' in response_data:
                    print(f"   💡 Hints: {response_data['hints']}")
                if 'conversation_state' in response_data:
                    print(f"   📊 State: {response_data['conversation_state']}")
                if 'updated_context' in response_data:
                    context = response_data['updated_context']
                    print(f"   📍 Context: Destination={context.get('destination')}, "
                          f"Dates={context.get('dates')}, Travelers={context.get('travelers')}")
            else:
                print("Failed to send message")
                break

async def check_server_health():
    """Check if the server is running."""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to access the API root or sessions endpoint
            async with session.get(f"{API_BASE_URL}/travel/sessions", timeout=aiohttp.ClientTimeout(total=5)) as response:
                # Even a 401/403 means the server is running
                if response.status in [200, 401, 403, 405]:
                    print("✅ Server is running")
                    return True
                else:
                    print(f"❌ Server returned unexpected status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        return False

async def main():
    """Main test function."""
    print("AI Chat API Integration Test")
    print("============================")
    print(f"Testing against: {API_BASE_URL}")
    
    # Check server health
    if not await check_server_health():
        print("\n⚠️  Please make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8001")
        return
    
    # Run conversation tests
    await test_conversation()
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)
    print("\nIf you see repetitive responses like 'I understand. How can I help you plan your trip?'")
    print("for every message, then the AI orchestrator is not properly connected.")
    print("\nTo enable AI responses:")
    print("1. Set up LLM credentials in your .env file")
    print("2. Choose a provider: OPENAI_API_KEY, AZURE_OPENAI_*, or ANTHROPIC_API_KEY")
    print("3. Set LLM_PROVIDER to match your chosen provider")
    print("4. Restart the backend server")

if __name__ == "__main__":
    asyncio.run(main())