"""
Test script to check AI response suggestions
"""
import asyncio
import httpx
import json

async def test_ai_suggestions():
    """Test AI chat response to see what suggestions are returned"""
    base_url = "http://localhost:8001"
    
    # Test session creation and chat
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a session with initial message
        print("Creating session...")
        session_response = await client.post(
            f"{base_url}/api/v1/travel/sessions",
            json={
                "message": "I want to plan a trip to Tokyo",
                "source": "web"
            }
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            print("\nSession created successfully!")
            print(f"Session ID: {session_data.get('session_id')}")
            print("\nFull response:")
            print(json.dumps(session_data, indent=2))
            
            # Extract suggestions from various places
            print("\n" + "="*50)
            print("SUGGESTIONS ANALYSIS:")
            print("="*50)
            
            # Check direct suggestions
            if 'suggestions' in session_data:
                print(f"\nDirect suggestions: {session_data['suggestions']}")
            
            # Check metadata
            if 'metadata' in session_data:
                print(f"\nMetadata: {session_data['metadata']}")
                
            # Check in data.metadata
            if 'data' in session_data and isinstance(session_data['data'], dict):
                if 'metadata' in session_data['data']:
                    print(f"\nData.metadata: {session_data['data']['metadata']}")
                    
            # Check conversation history for AI message metadata
            if 'conversation_history' in session_data:
                for msg in session_data['conversation_history']:
                    if msg.get('role') == 'assistant':
                        print(f"\nAI message metadata: {msg.get('metadata', {})}")
                        
            # Now test sending a follow-up message
            session_id = session_data.get('session_id')
            if session_id:
                print("\n" + "="*50)
                print("Sending follow-up message...")
                chat_response = await client.post(
                    f"{base_url}/api/v1/travel/sessions/{session_id}/chat",
                    json={
                        "message": "I want to go next month for 7 days"
                    }
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print("\nChat response received!")
                    print("\nFull chat response:")
                    print(json.dumps(chat_data, indent=2))
                    
                    # Extract AI response details
                    if 'ai_response' in chat_data:
                        ai_resp = chat_data['ai_response']
                        print(f"\n\nAI Response metadata: {ai_resp.get('metadata', {})}")
                        
                else:
                    print(f"Chat request failed: {chat_response.status_code}")
                    print(chat_response.text)
        else:
            print(f"Session creation failed: {session_response.status_code}")
            print(session_response.text)

if __name__ == "__main__":
    asyncio.run(test_ai_suggestions())