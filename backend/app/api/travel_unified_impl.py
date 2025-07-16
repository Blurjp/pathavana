"""
Implementation of the unified travel API endpoints.
This provides the actual functionality for the travel_unified routes.
"""

import uuid
import json
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.travel import (
    TravelSessionCreate,
    TravelSessionResponse,
    ChatRequest,
    SearchRequest,
    SaveItemRequest,
    SessionUpdate,
    LocationUpdate,
    DateUpdate,
    SessionStatus,
    MessageRole,
    SearchType
)
from ..schemas.base import BaseResponse, ResponseMetadata, ErrorDetail
from ..core.logger import logger


# In-memory storage for development (replace with database in production)
SESSIONS_STORE: Dict[str, Dict[str, Any]] = {}


class TravelSessionManager:
    """Manages travel sessions with in-memory storage for development."""
    
    @staticmethod
    async def create_session(
        user: Dict[str, Any],
        request: TravelSessionCreate
    ) -> Dict[str, Any]:
        """Create a new travel session."""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "id": session_id,
            "user_id": user.get("id"),
            "user_email": user.get("email"),
            "status": SessionStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "trip_context": {
                "initial_message": request.message,
                "source": request.source,
                "metadata": request.metadata or {},
                "destination": None,
                "dates": None,
                "travelers": None,
                "budget": None
            },
            "conversation_history": [
                {
                    "id": str(uuid.uuid4()),
                    "role": MessageRole.USER.value,
                    "content": request.message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"source": request.source}
                }
            ],
            "search_results": {},
            "selected_items": {},
            "preferences": {}
        }
        
        # Store session
        SESSIONS_STORE[session_id] = session_data
        
        # Generate initial AI response
        ai_response = await TravelSessionManager._generate_initial_response(request.message)
        session_data["conversation_history"].append(ai_response)
        
        # Extract context from message
        context_updates = await TravelSessionManager._extract_context(request.message)
        session_data["trip_context"].update(context_updates)
        
        return session_data
    
    @staticmethod
    async def get_session(session_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        session = SESSIONS_STORE.get(session_id)
        
        if not session:
            return None
        
        # Check user access
        if user_id is not None and session.get("user_id") != user_id:
            return None
        
        return session
    
    @staticmethod
    async def update_session(
        session_id: str,
        updates: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a session."""
        session = await TravelSessionManager.get_session(session_id, user_id)
        if not session:
            return None
        
        # Update allowed fields
        allowed_fields = ["status", "trip_context", "preferences"]
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "trip_context":
                    session["trip_context"].update(value)
                else:
                    session[field] = value
        
        session["updated_at"] = datetime.utcnow().isoformat()
        return session
    
    @staticmethod
    async def add_chat_message(
        session_id: str,
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a chat message and get AI response."""
        session = await TravelSessionManager.get_session(session_id, user_id)
        if not session:
            return None
        
        # Add user message
        user_message = {
            "id": str(uuid.uuid4()),
            "role": MessageRole.USER.value,
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": request.metadata or {}
        }
        session["conversation_history"].append(user_message)
        
        # Extract context from message
        context_updates = await TravelSessionManager._extract_context(request.message)
        session["trip_context"].update(context_updates)
        
        # Generate AI response
        ai_response = await TravelSessionManager._generate_ai_response(
            request.message,
            session["trip_context"],
            session.get("search_results", {})
        )
        session["conversation_history"].append(ai_response)
        
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "session": session
        }
    
    @staticmethod
    async def search(
        session_id: str,
        request: SearchRequest,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Perform a search and store results."""
        session = await TravelSessionManager.get_session(session_id, user_id)
        if not session:
            return None
        
        # Generate mock search results
        results = await TravelSessionManager._perform_search(
            request.search_type,
            session["trip_context"],
            request.filters
        )
        
        # Store results
        if "search_results" not in session:
            session["search_results"] = {}
        
        session["search_results"][request.search_type.value] = {
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": request.filters
        }
        
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "results": results,
            "total_count": len(results),
            "search_type": request.search_type.value
        }
    
    @staticmethod
    async def save_item(
        session_id: str,
        request: SaveItemRequest,
        user_id: Optional[int] = None
    ) -> bool:
        """Save an item to the session."""
        session = await TravelSessionManager.get_session(session_id, user_id)
        if not session:
            return False
        
        if "selected_items" not in session:
            session["selected_items"] = {}
        
        item_type = request.item_type.value
        if item_type not in session["selected_items"]:
            session["selected_items"][item_type] = []
        
        # Check if item already exists
        existing = next(
            (item for item in session["selected_items"][item_type] if item["id"] == request.item_id),
            None
        )
        
        if not existing:
            session["selected_items"][item_type].append({
                "id": request.item_id,
                "data": request.item_data,
                "selected_at": datetime.utcnow().isoformat()
            })
        
        session["updated_at"] = datetime.utcnow().isoformat()
        return True
    
    @staticmethod
    async def stream_chat(
        session_id: str,
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses."""
        session = await TravelSessionManager.get_session(session_id, user_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return
        
        # Add user message
        user_message = {
            "id": str(uuid.uuid4()),
            "role": MessageRole.USER.value,
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": request.metadata or {}
        }
        session["conversation_history"].append(user_message)
        
        # Stream AI response
        response_parts = [
            "I understand you want to ",
            "travel. Let me help you ",
            "plan your trip. ",
            "Based on your message, ",
            "I can assist with finding ",
            "flights, hotels, and activities. ",
            "What specific details would ",
            "you like to explore?"
        ]
        
        full_response = ""
        for part in response_parts:
            full_response += part
            yield f"data: {json.dumps({'content': part, 'type': 'content'})}\n\n"
            await asyncio.sleep(0.1)  # Simulate streaming delay
        
        # Add complete message to history
        ai_message = {
            "id": str(uuid.uuid4()),
            "role": MessageRole.ASSISTANT.value,
            "content": full_response,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"streamed": True}
        }
        session["conversation_history"].append(ai_message)
        
        # Send final message
        yield f"data: {json.dumps({'type': 'done', 'message_id': ai_message['id']})}\n\n"
    
    @staticmethod
    async def _generate_initial_response(message: str) -> Dict[str, Any]:
        """Generate initial AI response."""
        return {
            "id": str(uuid.uuid4()),
            "role": MessageRole.ASSISTANT.value,
            "content": (
                "I'd be happy to help you plan your trip! "
                "I can assist you with finding flights, hotels, and activities. "
                "Could you tell me more about where you'd like to go and when?"
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "suggestions": [
                    "Search for flights",
                    "Find hotels",
                    "Discover activities"
                ]
            }
        }
    
    @staticmethod
    async def _generate_ai_response(
        message: str,
        context: Dict[str, Any],
        search_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI response based on context."""
        # Simple response generation based on keywords
        response_content = "I understand. "
        
        if "flight" in message.lower():
            response_content += "Let me search for flights for you. "
        elif "hotel" in message.lower():
            response_content += "I'll help you find the perfect hotel. "
        elif "activity" in message.lower() or "things to do" in message.lower():
            response_content += "Let me show you some great activities. "
        
        # Add context-aware suggestions
        suggestions = []
        if not context.get("destination"):
            suggestions.append("Where would you like to travel?")
        if not context.get("dates"):
            suggestions.append("When are you planning to travel?")
        if not context.get("travelers"):
            suggestions.append("How many people will be traveling?")
        
        if suggestions:
            response_content += " ".join(suggestions)
        else:
            response_content += "I have all the information I need. Would you like me to search for options?"
        
        return {
            "id": str(uuid.uuid4()),
            "role": MessageRole.ASSISTANT.value,
            "content": response_content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "context_complete": all([
                    context.get("destination"),
                    context.get("dates"),
                    context.get("travelers")
                ]),
                "suggestions": [
                    "Search flights",
                    "Find hotels",
                    "Look for activities"
                ] if not suggestions else []
            }
        }
    
    @staticmethod
    async def _extract_context(message: str) -> Dict[str, Any]:
        """Extract travel context from message."""
        context = {}
        
        # Simple keyword extraction (replace with NLP in production)
        message_lower = message.lower()
        
        # Extract destination
        destinations = ["tokyo", "paris", "london", "new york", "rome", "barcelona"]
        for dest in destinations:
            if dest in message_lower:
                context["destination"] = dest.title()
                break
        
        # Extract dates (simple pattern)
        if "tomorrow" in message_lower:
            context["dates"] = {"start": "tomorrow", "flexible": True}
        elif "next week" in message_lower:
            context["dates"] = {"start": "next week", "flexible": True}
        elif "weekend" in message_lower:
            context["dates"] = {"start": "weekend", "flexible": True}
        
        # Extract travelers
        if "alone" in message_lower or "solo" in message_lower:
            context["travelers"] = 1
        elif "couple" in message_lower or "two" in message_lower:
            context["travelers"] = 2
        elif "family" in message_lower:
            context["travelers"] = 4
        
        return context
    
    @staticmethod
    async def _perform_search(
        search_type: SearchType,
        context: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform mock search (replace with real search in production)."""
        results = []
        
        if search_type == SearchType.FLIGHTS:
            results = [
                {
                    "id": f"flight-{i}",
                    "airline": ["United", "Delta", "American"][i % 3],
                    "departure": "JFK",
                    "arrival": context.get("destination", "LAX"),
                    "price": {"amount": 300 + (i * 50), "currency": "USD"},
                    "duration": f"{6 + i}h {30 - (i * 10)}m",
                    "stops": i % 2
                }
                for i in range(3)
            ]
        elif search_type == SearchType.HOTELS:
            results = [
                {
                    "id": f"hotel-{i}",
                    "name": ["Grand Hotel", "City Inn", "Luxury Resort"][i % 3],
                    "location": context.get("destination", "Downtown"),
                    "rating": 4.0 + (i * 0.2),
                    "price": {"amount": 150 + (i * 50), "currency": "USD"},
                    "amenities": ["wifi", "pool", "gym", "spa"][:i+2]
                }
                for i in range(3)
            ]
        elif search_type == SearchType.ACTIVITIES:
            results = [
                {
                    "id": f"activity-{i}",
                    "name": ["City Tour", "Museum Visit", "Food Tour"][i % 3],
                    "location": context.get("destination", "City Center"),
                    "duration": f"{2 + i} hours",
                    "price": {"amount": 50 + (i * 25), "currency": "USD"},
                    "rating": 4.5 - (i * 0.1)
                }
                for i in range(3)
            ]
        
        return results


# Update the travel_unified.py file to use this implementation
async def get_travel_service() -> TravelSessionManager:
    """Get travel service instance."""
    return TravelSessionManager()