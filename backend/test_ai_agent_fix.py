#!/usr/bin/env python3
"""
Test script to verify AI agent functionality after fixes.
This script tests both with and without LLM configuration.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Base URL for the API
API_BASE_URL = "http://localhost:8001/api/v1"


class Colors:
    """Terminal colors for output formatting."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")


async def check_llm_configuration() -> Dict[str, Any]:
    """Check the current LLM configuration."""
    print_header("Checking LLM Configuration")
    
    # Check environment variables
    config = {
        "provider": os.getenv("LLM_PROVIDER", "not_set"),
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "azure_key": bool(os.getenv("AZURE_OPENAI_API_KEY")),
        "azure_endpoint": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
        "azure_deployment": bool(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")),
        "anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY"))
    }
    
    print(f"LLM Provider: {config['provider']}")
    
    if config['provider'] == "openai":
        if config['openai_key']:
            print_success("OpenAI API key is configured")
        else:
            print_warning("OpenAI API key is NOT configured")
    elif config['provider'] == "azure_openai":
        if all([config['azure_key'], config['azure_endpoint'], config['azure_deployment']]):
            print_success("Azure OpenAI credentials are fully configured")
        else:
            print_warning("Azure OpenAI credentials are NOT fully configured")
            print(f"  - API Key: {'✓' if config['azure_key'] else '✗'}")
            print(f"  - Endpoint: {'✓' if config['azure_endpoint'] else '✗'}")
            print(f"  - Deployment: {'✓' if config['azure_deployment'] else '✗'}")
    elif config['provider'] == "anthropic":
        if config['anthropic_key']:
            print_success("Anthropic API key is configured")
        else:
            print_warning("Anthropic API key is NOT configured")
    else:
        print_error(f"Unknown LLM provider: {config['provider']}")
    
    return config


async def test_health_check(session: aiohttp.ClientSession) -> bool:
    """Test if the API is running."""
    print_header("Testing API Health Check")
    
    try:
        async with session.get(f"{API_BASE_URL}/") as response:
            if response.status == 200:
                data = await response.json()
                print_success(f"API is running: {data.get('message', 'OK')}")
                return True
            else:
                print_error(f"API returned status {response.status}")
                return False
    except aiohttp.ClientError as e:
        print_error(f"Failed to connect to API: {e}")
        print_info("Make sure the backend server is running on port 8001")
        return False


async def create_session(session: aiohttp.ClientSession) -> Optional[str]:
    """Create a new travel session."""
    print_header("Creating Travel Session")
    
    payload = {
        "message": "Hi, I want to plan a trip to Paris next month",
        "source": "test_script",
        "metadata": {"test": True}
    }
    
    try:
        async with session.post(
            f"{API_BASE_URL}/travel/sessions",
            json=payload
        ) as response:
            if response.status == 201:
                data = await response.json()
                if data.get("success"):
                    session_id = data["data"]["session_id"]
                    print_success(f"Created session: {session_id}")
                    
                    # Check the initial response
                    initial_response = data["data"].get("initial_response", "")
                    print(f"\nInitial AI Response: {initial_response[:200]}...")
                    
                    # Check if hints are present
                    if "metadata" in data["data"] and "hints" in data["data"]["metadata"]:
                        print_info(f"Hints provided: {len(data['data']['metadata']['hints'])}")
                    
                    return session_id
                else:
                    print_error(f"Failed to create session: {data.get('errors', [])}")
                    return None
            else:
                print_error(f"API returned status {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
                return None
    except Exception as e:
        print_error(f"Error creating session: {e}")
        return None


async def test_chat_message(session: aiohttp.ClientSession, session_id: str, message: str) -> Dict[str, Any]:
    """Send a chat message and analyze the response."""
    print(f"\n{Colors.OKCYAN}Sending message: {message}{Colors.ENDC}")
    
    payload = {
        "message": message,
        "metadata": {"test": True}
    }
    
    try:
        async with session.post(
            f"{API_BASE_URL}/travel/sessions/{session_id}/chat",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("success"):
                    response_data = data["data"]
                    ai_message = response_data.get("message", "")
                    
                    print(f"AI Response: {ai_message[:300]}...")
                    
                    # Analyze response quality
                    analysis = {
                        "length": len(ai_message),
                        "is_template": "I understand." in ai_message,
                        "has_hints": "hints" in response_data,
                        "has_suggestions": bool(response_data.get("suggestions")),
                        "has_context": bool(response_data.get("updated_context")),
                        "mentions_destination": any(dest in ai_message.lower() for dest in ["paris", "tokyo", "london"])
                    }
                    
                    return {
                        "success": True,
                        "response": ai_message,
                        "data": response_data,
                        "analysis": analysis
                    }
                else:
                    print_error(f"Chat failed: {data.get('errors', [])}")
                    return {"success": False, "error": data.get('errors', [])}
            else:
                print_error(f"API returned status {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
                return {"success": False, "error": f"HTTP {response.status}"}
    except Exception as e:
        print_error(f"Error sending message: {e}")
        return {"success": False, "error": str(e)}


async def analyze_responses(responses: list) -> None:
    """Analyze the quality of AI responses."""
    print_header("Response Quality Analysis")
    
    template_count = sum(1 for r in responses if r.get("analysis", {}).get("is_template"))
    avg_length = sum(r.get("analysis", {}).get("length", 0) for r in responses) / len(responses) if responses else 0
    
    print(f"Total responses analyzed: {len(responses)}")
    print(f"Template responses: {template_count}/{len(responses)} ({template_count/len(responses)*100:.1f}%)")
    print(f"Average response length: {avg_length:.0f} characters")
    
    if template_count == len(responses):
        print_warning("All responses appear to be template-based (no AI)")
        print_info("This indicates the AI orchestrator is not working properly")
    elif template_count > 0:
        print_warning(f"Some responses are template-based ({template_count}/{len(responses)})")
    else:
        print_success("All responses appear to be AI-generated")
    
    # Check for context awareness
    context_aware = sum(1 for r in responses if r.get("analysis", {}).get("mentions_destination"))
    if context_aware > 0:
        print_success(f"Context awareness detected in {context_aware}/{len(responses)} responses")
    else:
        print_warning("No context awareness detected in responses")


async def main():
    """Run all tests."""
    print_header("AI Agent Functionality Test")
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check LLM configuration
    config = await check_llm_configuration()
    
    # Set up HTTP session
    async with aiohttp.ClientSession() as session:
        # Test health check
        if not await test_health_check(session):
            print_error("Cannot proceed without API connection")
            return
        
        # Create a session
        session_id = await create_session(session)
        if not session_id:
            print_error("Cannot proceed without a valid session")
            return
        
        # Test various chat messages
        print_header("Testing Chat Interactions")
        
        test_messages = [
            "I want to visit Tokyo instead",
            "What's the weather like there?",
            "Can you find flights from New York?",
            "I need a hotel near the city center",
            "What activities do you recommend?",
            "My budget is around $3000",
            "I'll be traveling with my family of 4"
        ]
        
        responses = []
        for msg in test_messages:
            await asyncio.sleep(1)  # Small delay between messages
            result = await test_chat_message(session, session_id, msg)
            if result.get("success"):
                responses.append(result)
        
        # Analyze responses
        await analyze_responses(responses)
        
        # Final verdict
        print_header("Test Summary")
        
        if all(r.get("analysis", {}).get("is_template") for r in responses):
            print_error("AI Agent is NOT working properly - only template responses")
            print_info("Recommended actions:")
            print("  1. Check LLM credentials in backend/.env")
            print("  2. Ensure the selected LLM provider has valid API keys")
            print("  3. Check backend logs for specific error messages")
            print("  4. Try switching to a different LLM provider (openai/anthropic)")
        else:
            print_success("AI Agent is working properly with intelligent responses!")
            
            # Check response quality
            avg_length = sum(r.get("analysis", {}).get("length", 0) for r in responses) / len(responses)
            if avg_length < 50:
                print_warning("Responses seem quite short, consider checking LLM configuration")
            
            hint_count = sum(1 for r in responses if r.get("analysis", {}).get("has_hints"))
            if hint_count > 0:
                print_success(f"Hint system is working ({hint_count}/{len(responses)} responses with hints)")


if __name__ == "__main__":
    asyncio.run(main())