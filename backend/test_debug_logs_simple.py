"""
Simple demonstration of debug logging for AI agent conversation flow.
This script shows how the AI agent processes messages without database dependencies.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime

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

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_debug.db"

def demonstrate_debug_flow():
    """Demonstrate the debug flow without async complexity."""
    print("\n" + "="*80)
    print("AI AGENT DEBUG LOG DEMONSTRATION")
    print("="*80)
    print("This test shows the debug logs for AI agent message processing.")
    print("="*80 + "\n")
    
    from app.core.logger import logger
    
    # Simulate the message processing flow
    print("📝 SCENARIO: User wants to plan a trip to Paris")
    print("-" * 60 + "\n")
    
    # 1. API Endpoint receives message
    logger.debug("\n" + "="*60)
    logger.debug("🗨️  PROCESSING CHAT MESSAGE")
    logger.debug(f"Session ID: 25417046-e7b2-467f-91aa-e09284a5b2f1")
    logger.debug(f"User message: Plan a weekend trip to Paris")
    logger.debug(f"Orchestrator available: False (using template responses)")
    logger.debug("="*60)
    
    # 2. Travel Session Manager processes message
    logger.debug(f"\n🔄 add_chat_message called for session 25417046-e7b2-467f-91aa-e09284a5b2f1")
    logger.debug(f"   User message: 'Plan a weekend trip to Paris'")
    logger.debug(f"   Orchestrator provided: False")
    logger.debug(f"   Conversation history length: 0")
    logger.debug(f"   Added user message to history")
    
    # 3. Context extraction
    logger.debug(f"   Extracting context from message...")
    logger.debug(f"   _extract_context called for: 'Plan a weekend trip to Paris'")
    logger.debug(f"      Found destination: Paris")
    logger.debug(f"      Found date: weekend")
    logger.debug(f"   Context updates: {{'destination': 'Paris', 'dates': {{'start': 'weekend', 'flexible': True}}}}")
    logger.debug(f"   Updated trip context: {{'destination': 'Paris', 'dates': {{'start': 'weekend', 'flexible': True}}, 'travelers': None}}")
    
    # 4. AI Response generation
    logger.debug(f"   Generating AI response...")
    logger.debug("\n" + "-"*40)
    logger.debug("🤖 _generate_ai_response called")
    logger.debug(f"   Message: 'Plan a weekend trip to Paris'")
    logger.debug(f"   Context: {{'destination': 'Paris', 'dates': {{'start': 'weekend', 'flexible': True}}, 'travelers': None}}")
    logger.debug(f"   Has orchestrator: False")
    logger.debug("-"*40)
    
    logger.debug("📋 Using template-based response (no orchestrator)")
    logger.debug("   _generate_template_response called")
    
    # 5. Hint generation
    logger.debug(f"\n   Final response content: 'I understand. How many people will be traveling?'")
    logger.debug("   Generating hints...")
    logger.debug(f"   Hints generated: 5 hints")
    
    # 6. Complete
    logger.debug(f"   AI response generated: 'I understand. How many people will be traveling?'")
    logger.debug(f"   Session updated and committed")
    logger.debug(f"✅ add_chat_message completed successfully")
    
    print("\n\n📊 CONVERSATION FLOW VISUALIZATION")
    print("=" * 60)
    print("""
    User Input: "Plan a weekend trip to Paris"
           |
           v
    [API Endpoint: /sessions/{id}/chat]
           |
           v
    [Travel Session Manager]
           |
           +---> Extract Context: {destination: "Paris", dates: "weekend"}
           |
           +---> Check Orchestrator: Not Available
           |
           +---> Generate Template Response
           |
           +---> Add Hints for User Guidance
           |
           v
    AI Response: "I understand. How many people will be traveling?"
    """)
    
    print("\n\n🔄 SECOND MESSAGE: 'Just me traveling alone'")
    print("-" * 60)
    
    # Process second message
    logger.debug(f"\n🔄 add_chat_message called for session 25417046-e7b2-467f-91aa-e09284a5b2f1")
    logger.debug(f"   User message: 'Just me traveling alone'")
    logger.debug(f"   Orchestrator provided: False")
    logger.debug(f"   Conversation history length: 2")
    logger.debug(f"   Extracting context from message...")
    logger.debug(f"   _extract_context called for: 'Just me traveling alone'")
    logger.debug(f"      Found travelers: 1 (solo)")
    logger.debug(f"   Context updates: {{'travelers': 1}}")
    logger.debug(f"   Updated trip context: {{'destination': 'Paris', 'dates': {{'start': 'weekend', 'flexible': True}}, 'travelers': 1}}")
    
    logger.debug("\n" + "-"*40)
    logger.debug("🤖 _generate_ai_response called")
    logger.debug(f"   Context: {{'destination': 'Paris', 'dates': {{'start': 'weekend', 'flexible': True}}, 'travelers': 1}}")
    logger.debug(f"   Has orchestrator: False")
    logger.debug("📋 Using template-based response (no orchestrator)")
    logger.debug(f"\n   Final response content: 'I understand. I have all the information I need. Would you like me to search for options?'")
    
    print("\n\n💡 KEY INSIGHTS FROM DEBUG LOGS")
    print("=" * 60)
    print("""
    1. WITHOUT ORCHESTRATOR (Template Responses):
       - Simple keyword matching for context extraction
       - Fixed response templates based on missing information
       - Limited understanding of user intent
       - Repetitive responses for similar inputs
    
    2. WITH ORCHESTRATOR (AI Responses):
       - Natural language understanding using LLM
       - Context-aware, dynamic responses
       - Better intent recognition
       - Varied and helpful responses
    
    3. DEBUG LOG BENEFITS:
       - Track exact message flow through the system
       - See context extraction in real-time
       - Understand why certain responses are generated
       - Identify when fallback mechanisms are used
       - Debug integration issues between components
    """)
    
    print("\n" + "="*80)
    print("To see these debug logs in your actual application:")
    print("1. Set logging level to DEBUG in your environment")
    print("2. Configure LLM credentials to enable AI responses")
    print("3. Watch the logs as users interact with the chat")
    print("="*80 + "\n")

if __name__ == "__main__":
    demonstrate_debug_flow()