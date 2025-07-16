"""
Database-backed implementation of the travel session manager.
Replaces in-memory storage with persistent PostgreSQL storage.
"""

import uuid
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# Import models after base to ensure proper registry
from ..models import Base, UnifiedTravelSession, User
from ..schemas.travel import (
    TravelSessionCreate,
    ChatRequest,
    SearchRequest,
    SaveItemRequest,
    SessionStatus,
    MessageRole,
    SearchType
)
from ..core.logger import logger
from .hint_generator import DynamicHintGenerator, ConversationState
from .travel_hints import EnhancedHintGenerator


class DatabaseTravelSessionManager:
    """Manages travel sessions with database persistence."""
    
    def __init__(self, db: AsyncSession, orchestrator=None):
        self.db = db
        self.hint_generator = EnhancedHintGenerator()
        self.orchestrator = orchestrator
    
    async def create_empty_session(
        self,
        user: Optional[User]
    ) -> UnifiedTravelSession:
        """Create a new empty travel session without initial message."""
        try:
            # Create minimal session data
            session_data = {
                "conversation_history": [],
                "ui_state": {
                    "current_step": "initial",
                    "source": "web"
                },
                "parsed_intent": {}
            }
            
            plan_data = {
                "initial_message": "",
                "trip_context": {
                    "destination": None,
                    "dates": None,
                    "travelers": None,
                    "budget": None
                },
                "search_results": {},
                "selected_items": {},
                "preferences": {}
            }
            
            # Create session in database
            session = UnifiedTravelSession(
                user_id=user.id if user else None,
                status=SessionStatus.ACTIVE.value,
                session_data=session_data,
                plan_data=plan_data,
                session_metadata={
                    "source": "web",
                    "created_from": "empty_session",
                    "version": "2.0"
                },
                last_activity_at=datetime.utcnow()
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Created new empty travel session: {session.session_id}")
            return session
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating empty session: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating empty session: {e}")
            raise
    
    async def create_session(
        self,
        user: Optional[User],
        request: TravelSessionCreate,
        orchestrator: Optional[Any] = None
    ) -> UnifiedTravelSession:
        """Create a new travel session in the database."""
        try:
            # Generate initial conversation
            initial_conversation = [
                {
                    "id": str(uuid.uuid4()),
                    "role": MessageRole.USER.value,
                    "content": request.message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"source": request.source}
                }
            ]
            
            # Generate initial AI response with orchestrator
            if orchestrator:
                ai_response = await self._generate_ai_response(
                    request.message,
                    {},  # Empty context for initial message
                    {},  # No search results yet
                    [],  # No conversation history yet
                    orchestrator
                )
            else:
                # Fallback for initial response if no orchestrator
                ai_response = await self._generate_initial_response(request.message)
            initial_conversation.append(ai_response)
            
            # Extract context from message
            context_data = await self._extract_context(request.message)
            
            # Create session data
            session_data = {
                "conversation_history": initial_conversation,
                "ui_state": {
                    "current_step": "initial",
                    "source": request.source
                },
                "parsed_intent": context_data
            }
            
            plan_data = {
                "initial_message": request.message,
                "trip_context": {
                    "destination": context_data.get("destination"),
                    "dates": context_data.get("dates"),
                    "travelers": context_data.get("travelers"),
                    "budget": context_data.get("budget")
                },
                "search_results": {},
                "selected_items": {},
                "preferences": {}
            }
            
            # Create session in database
            session = UnifiedTravelSession(
                user_id=user.id if user else None,
                status=SessionStatus.ACTIVE.value,
                session_data=session_data,
                plan_data=plan_data,
                session_metadata={
                    "source": request.source,
                    "created_from": request.metadata or {},
                    "version": "2.0"
                },
                last_activity_at=datetime.utcnow()
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Created new travel session: {session.session_id}")
            return session
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating session: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(
        self,
        session_id: str,
        user_id: Optional[int] = None
    ) -> Optional[UnifiedTravelSession]:
        """Get a session by ID from the database."""
        try:
            query = select(UnifiedTravelSession).where(
                UnifiedTravelSession.session_id == session_id
            )
            
            # Add user filter if provided
            if user_id is not None:
                query = query.where(UnifiedTravelSession.user_id == user_id)
            
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()
            
            if session:
                # Update last activity
                session.last_activity_at = datetime.utcnow()
                await self.db.commit()
            
            return session
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting session {session_id}: {e}")
            return None
    
    async def get_or_create_session(
        self,
        session_id: str,
        user: Optional[User],
        initial_message: str = "I want to plan a trip"
    ) -> UnifiedTravelSession:
        """Get an existing session or create a new one if it doesn't exist."""
        # Try to get existing session
        session = await self.get_session(session_id, user.id if user else None)
        
        if session:
            return session
        
        # Create new session with the same ID if not found
        logger.info(f"Session {session_id} not found, creating new session with same ID")
        
        try:
            # Generate initial conversation
            initial_conversation = [
                {
                    "id": str(uuid.uuid4()),
                    "role": MessageRole.USER.value,
                    "content": initial_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"source": "web", "recovered": True}
                }
            ]
            
            # Generate initial AI response
            ai_response = await self._generate_initial_response(initial_message)
            initial_conversation.append(ai_response)
            
            # Extract context from message
            context_data = await self._extract_context(initial_message)
            
            # Create session data
            session_data = {
                "conversation_history": initial_conversation,
                "ui_state": {
                    "current_step": "initial",
                    "source": "web"
                },
                "parsed_intent": context_data
            }
            
            plan_data = {
                "initial_message": initial_message,
                "trip_context": {
                    "destination": context_data.get("destination"),
                    "dates": context_data.get("dates"),
                    "travelers": context_data.get("travelers"),
                    "budget": context_data.get("budget")
                },
                "search_results": {},
                "selected_items": {},
                "preferences": {}
            }
            
            # Create session in database with specific ID
            session = UnifiedTravelSession(
                session_id=session_id,  # Use the provided session ID
                user_id=user.id if user else None,
                status=SessionStatus.ACTIVE.value,
                session_data=session_data,
                plan_data=plan_data,
                session_metadata={
                    "source": "web",
                    "recovered": True,
                    "version": "2.0"
                },
                last_activity_at=datetime.utcnow()
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Created recovered travel session: {session.session_id}")
            return session
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating recovered session: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating recovered session: {e}")
            raise
    
    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[UnifiedTravelSession]:
        """Update a session in the database."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            # Update allowed fields
            if "status" in updates:
                session.status = updates["status"]
            
            if "trip_context" in updates and session.plan_data:
                session.plan_data["trip_context"].update(updates["trip_context"])
            
            if "preferences" in updates and session.plan_data:
                session.plan_data["preferences"] = updates["preferences"]
            
            if "session_data" in updates:
                session.session_data.update(updates["session_data"])
            
            session.last_activity_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(session)
            
            return session
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating session {session_id}: {e}")
            return None
    
    async def add_chat_message(
        self,
        session_id: str,
        request: ChatRequest,
        user_id: Optional[int] = None,
        orchestrator: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a chat message and get AI response."""
        logger.debug(f"\n🔄 add_chat_message called for session {session_id}")
        logger.debug(f"   User message: '{request.message}'")
        logger.debug(f"   Orchestrator provided: {orchestrator is not None}")
        
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return None
            
            # Get conversation history
            conversation_history = session.session_data.get("conversation_history", [])
            logger.debug(f"   Conversation history length: {len(conversation_history)}")
            
            # Add user message
            user_message = {
                "id": str(uuid.uuid4()),
                "role": MessageRole.USER.value,
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": request.metadata or {}
            }
            conversation_history.append(user_message)
            logger.debug(f"   Added user message to history")
            
            # Extract context from message
            logger.debug(f"   Extracting context from message...")
            context_updates = await self._extract_context(request.message)
            logger.debug(f"   Context updates: {context_updates}")
            
            # Update trip context
            if session.plan_data and "trip_context" in session.plan_data:
                session.plan_data["trip_context"].update(context_updates)
                logger.debug(f"   Updated trip context: {session.plan_data['trip_context']}")
            
            # Generate AI response
            logger.debug(f"   Generating AI response...")
            ai_response = await self._generate_ai_response(
                request.message,
                session.plan_data.get("trip_context", {}) if session.plan_data else {},
                session.plan_data.get("search_results", {}) if session.plan_data else {},
                conversation_history,
                orchestrator
            )
            conversation_history.append(ai_response)
            logger.debug(f"   AI response generated: '{ai_response['content'][:100]}...'")
            
            # Update session data
            session.session_data["conversation_history"] = conversation_history
            session.last_activity_at = datetime.utcnow()
            
            # Mark session as dirty to ensure JSONB update is detected
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "session_data")
            flag_modified(session, "plan_data")
            
            await self.db.commit()
            logger.debug(f"   Session updated and committed")
            
            result = {
                "user_message": user_message,
                "ai_response": ai_response,
                "session": {
                    "session_id": session.session_id,
                    "status": session.status,
                    "session_data": session.session_data,
                    "plan_data": session.plan_data
                }
            }
            
            logger.debug(f"✅ add_chat_message completed successfully")
            return result
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error adding chat message: {e}")
            return None
    
    async def search(
        self,
        session_id: str,
        request: SearchRequest,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Perform a search and store results."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            # Generate search results
            results = await self._perform_search(
                request.search_type,
                session.plan_data.get("trip_context", {}) if session.plan_data else {},
                request.filters
            )
            
            # Store results in plan_data
            if not session.plan_data:
                session.plan_data = {}
            
            if "search_results" not in session.plan_data:
                session.plan_data["search_results"] = {}
            
            session.plan_data["search_results"][request.search_type.value] = {
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
                "filters": request.filters
            }
            
            session.last_activity_at = datetime.utcnow()
            
            # Mark as dirty for JSONB update
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "plan_data")
            
            await self.db.commit()
            
            return {
                "results": results,
                "total_count": len(results),
                "search_type": request.search_type.value
            }
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error performing search: {e}")
            return None
    
    async def save_item(
        self,
        session_id: str,
        request: SaveItemRequest,
        user_id: Optional[int] = None
    ) -> bool:
        """Save an item to the session."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            if not session.plan_data:
                session.plan_data = {}
            
            if "selected_items" not in session.plan_data:
                session.plan_data["selected_items"] = {}
            
            item_type = request.item_type.value
            if item_type not in session.plan_data["selected_items"]:
                session.plan_data["selected_items"][item_type] = []
            
            # Check if item already exists
            existing = next(
                (item for item in session.plan_data["selected_items"][item_type]
                 if item["id"] == request.item_id),
                None
            )
            
            if not existing:
                session.plan_data["selected_items"][item_type].append({
                    "id": request.item_id,
                    "data": request.item_data,
                    "selected_at": datetime.utcnow().isoformat()
                })
            
            session.last_activity_at = datetime.utcnow()
            
            # Mark as dirty for JSONB update
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "plan_data")
            
            await self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error saving item: {e}")
            return False
    
    async def stream_chat(
        self,
        session_id: str,
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses."""
        session = await self.get_session(session_id, user_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return
        
        try:
            # Get conversation history
            conversation_history = session.session_data.get("conversation_history", [])
            
            # Add user message
            user_message = {
                "id": str(uuid.uuid4()),
                "role": MessageRole.USER.value,
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": request.metadata or {}
            }
            conversation_history.append(user_message)
            
            # Extract context from message
            context_updates = await self._extract_context(request.message)
            
            # Update trip context
            if session.plan_data and "trip_context" in session.plan_data:
                session.plan_data["trip_context"].update(context_updates)
            
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
                import asyncio
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Generate AI message with hints
            context = session.plan_data.get("trip_context", {}) if session.plan_data else {}
            hint_response = self.hint_generator.create_response_with_hints(
                message=request.message,
                conversation_history=conversation_history[:-1],  # Exclude the just-added user message
                current_context=context,
                base_response=full_response
            )
            
            # Add complete message to history with hints
            ai_message = {
                "id": str(uuid.uuid4()),
                "role": MessageRole.ASSISTANT.value,
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "streamed": True,
                    "hints": hint_response.get("hints", []),
                    "conversation_state": hint_response.get("conversation_state"),
                    "extracted_entities": hint_response.get("extracted_entities", []),
                    "next_steps": hint_response.get("next_steps", [])
                }
            }
            conversation_history.append(ai_message)
            
            # Update session
            session.session_data["conversation_history"] = conversation_history
            session.last_activity_at = datetime.utcnow()
            
            # Mark as dirty
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "session_data")
            
            await self.db.commit()
            
            # Send hints before completion
            if hint_response.get("hints"):
                yield f"data: {json.dumps({'type': 'hints', 'hints': hint_response['hints']})}\n\n"
            
            # Send metadata
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_state': hint_response.get('conversation_state'), 'next_steps': hint_response.get('next_steps', [])})}\n\n"
            
            # Send final message
            yield f"data: {json.dumps({'type': 'done', 'message_id': ai_message['id']})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': 'Stream error', 'message': str(e)})}\n\n"
    
    # Helper methods remain the same
    async def _generate_initial_response(self, message: str) -> Dict[str, Any]:
        """Generate initial AI response with hints (fallback when no orchestrator)."""
        # This should only be used as a fallback during session creation
        # when orchestrator is not available
        logger.warning("Using fallback initial response - orchestrator not available during session creation")
        base_content = (
            "AI service is initializing. Please send your travel planning request again to get personalized assistance."
        )
        
        # Extract initial context
        initial_context = await self._extract_context(message)
        
        # Generate hints for initial response
        hint_response = self.hint_generator.create_response_with_hints(
            message=message,
            conversation_history=[],
            current_context=initial_context,
            base_response=base_content
        )
        
        return {
            "id": str(uuid.uuid4()),
            "role": MessageRole.ASSISTANT.value,
            "content": hint_response["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "suggestions": [
                    "Search for flights",
                    "Find hotels",
                    "Discover activities"
                ],
                "hints": hint_response.get("hints", []),
                "conversation_state": hint_response.get("conversation_state", "initial"),
                "extracted_entities": hint_response.get("extracted_entities", []),
                "next_steps": hint_response.get("next_steps", [])
            }
        }
    
    async def _generate_ai_response(
        self,
        message: str,
        context: Dict[str, Any],
        search_results: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        orchestrator: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Generate AI response based on context with hints."""
        logger.debug("\n" + "-"*40)
        logger.debug("🤖 _generate_ai_response called")
        logger.debug(f"   Message: '{message}'")
        logger.debug(f"   Context: {context}")
        logger.debug(f"   Has orchestrator: {orchestrator is not None}")
        logger.debug("-"*40)
        
        response_content = ""
        metadata = {}
        
        # Orchestrator is required for AI responses
        if not orchestrator:
            logger.error("❌ AI Orchestrator not available - cannot generate AI response")
            raise RuntimeError(
                "AI service is not configured. Please set up OpenAI API credentials in the backend .env file. "
                "Required: OPENAI_API_KEY or AZURE_OPENAI_API_KEY with related settings."
            )
        
        logger.debug("🎨 Using AI Orchestrator for response generation")
        try:
            # Use the orchestrator to process the message
            logger.debug("   Calling orchestrator.process_message()...")
            orchestrator_response = await orchestrator.process_message(
                message=message,
                session_id=None,  # Let orchestrator handle session internally
                user_id=None,
                stream=False
            )
            
            # Extract content from orchestrator response
            logger.debug(f"   Orchestrator response received: {list(orchestrator_response.keys()) if orchestrator_response else 'None'}")
            
            if orchestrator_response and "response" in orchestrator_response:
                response_content = orchestrator_response["response"]
                logger.debug(f"   Response content: '{response_content[:100]}...'")
                
                # Include additional metadata from the orchestrator
                if "context" in orchestrator_response:
                    metadata["updated_context"] = orchestrator_response["context"]
                    logger.debug(f"   Context from orchestrator: {orchestrator_response['context']}")
                if "suggestions" in orchestrator_response:
                    metadata["orchestrator_suggestions"] = orchestrator_response["suggestions"]
                    logger.debug(f"   Suggestions: {orchestrator_response['suggestions']}")
                if "clarifying_questions" in orchestrator_response:
                    metadata["clarifying_questions"] = orchestrator_response["clarifying_questions"]
                if "context_validation" in orchestrator_response:
                    metadata["context_validation"] = orchestrator_response["context_validation"]
                if "tools_used" in orchestrator_response:
                    metadata["tools_used"] = orchestrator_response["tools_used"]
                    logger.debug(f"   Tools used: {orchestrator_response['tools_used']}")
            else:
                raise ValueError("Invalid orchestrator response format")
                
        except RuntimeError:
            # Re-raise configuration errors
            raise
        except Exception as e:
            logger.error(f"❌ Orchestrator failed with error: {e}")
            logger.debug(f"   Error type: {type(e).__name__}")
            logger.debug(f"   Error details: {str(e)}")
            # Re-raise the error instead of falling back
            raise RuntimeError(f"AI service error: {str(e)}")
        
        logger.debug(f"\n   Final response content: '{response_content[:100]}...'")
        
        # Generate hints using the hint generator
        logger.debug("   Generating hints...")
        hint_response = self.hint_generator.create_response_with_hints(
            message=message,
            conversation_history=conversation_history or [],
            current_context=context,
            base_response=response_content
        )
        logger.debug(f"   Hints generated: {len(hint_response.get('hints', []))} hints")
        
        # Merge orchestrator metadata with hint metadata
        final_metadata = {
            "context_complete": all([
                context.get("destination"),
                context.get("dates"),
                context.get("travelers")
            ]),
            "suggestions": [
                "Search flights",
                "Find hotels",
                "Look for activities"
            ] if all([context.get("destination"), context.get("dates"), context.get("travelers")]) else [],
            "hints": hint_response.get("hints", []),
            "conversation_state": hint_response.get("conversation_state"),
            "extracted_entities": hint_response.get("extracted_entities", []),
            "context_summary": hint_response.get("context_summary", {}),
            "next_steps": hint_response.get("next_steps", [])
        }
        
        # Include any orchestrator metadata
        final_metadata.update(metadata)
        
        return {
            "id": str(uuid.uuid4()),
            "role": MessageRole.ASSISTANT.value,
            "content": hint_response["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": final_metadata
        }
    
    # Remove template response method - all responses must come from AI
    # def _generate_template_response(self, message: str, context: Dict[str, Any]) -> str:
    #     """Removed - all responses must come from AI orchestrator"""
    
    async def _extract_context(self, message: str) -> Dict[str, Any]:
        """Extract travel context from message."""
        logger.debug(f"   _extract_context called for: '{message}'")
        context = {}
        
        # Simple keyword extraction (replace with NLP in production)
        message_lower = message.lower()
        
        # Extract destination
        destinations = ["tokyo", "paris", "london", "new york", "rome", "barcelona"]
        for dest in destinations:
            if dest in message_lower:
                context["destination"] = dest.title()
                logger.debug(f"      Found destination: {dest.title()}")
                break
        
        # Extract dates (simple pattern)
        if "tomorrow" in message_lower:
            context["dates"] = {"start": "tomorrow", "flexible": True}
            logger.debug(f"      Found date: tomorrow")
        elif "next week" in message_lower:
            context["dates"] = {"start": "next week", "flexible": True}
            logger.debug(f"      Found date: next week")
        elif "weekend" in message_lower:
            context["dates"] = {"start": "weekend", "flexible": True}
            logger.debug(f"      Found date: weekend")
        
        # Extract travelers
        if "alone" in message_lower or "solo" in message_lower:
            context["travelers"] = 1
            logger.debug(f"      Found travelers: 1 (solo)")
        elif "couple" in message_lower or "two" in message_lower:
            context["travelers"] = 2
            logger.debug(f"      Found travelers: 2 (couple)")
        elif "family" in message_lower:
            context["travelers"] = 4
            logger.debug(f"      Found travelers: 4 (family)")
        
        if not context:
            logger.debug(f"      No context extracted from message")
        
        return context
    
    async def _perform_search(
        self,
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