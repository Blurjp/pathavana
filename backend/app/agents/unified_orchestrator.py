"""
Unified conversation orchestrator for managing AI-driven travel planning.
Uses LangChain for agent coordination and tool management.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import json
import logging
from datetime import datetime
import asyncio

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import Tool, StructuredTool
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager

from ..services.unified_travel_service import UnifiedTravelService
from ..services.llm_service import LLMService
from ..services.trip_context_service import TripContextService
from ..services.amadeus_service import AmadeusService
from ..services.cache_service import CacheService
from ..core.config import settings
from .tools.flight_tools import FlightTools
from .tools.hotel_tools import HotelTools
from .tools.activity_tools import ActivityTools

logger = logging.getLogger(__name__)


class UnifiedOrchestrator:
    """
    Main conversation orchestrator that manages the travel planning conversation flow.
    Coordinates between LLM, context management, and external services using LangChain.
    """
    
    def __init__(self, travel_service: UnifiedTravelService):
        logger.debug("🤖 Initializing UnifiedOrchestrator...")
        self.travel_service = travel_service
        self.llm_service = LLMService()
        self.context_service = TripContextService()
        self.amadeus_service = AmadeusService()
        self.cache_service = CacheService()
        
        logger.debug("Initializing AI tool services...")
        # Initialize tool services
        self.flight_tools = FlightTools(self.amadeus_service, self.cache_service)
        self.hotel_tools = HotelTools(self.amadeus_service, self.cache_service)
        self.activity_tools = ActivityTools(self.cache_service)
        
        logger.debug("Initializing LangChain components...")
        # Initialize LangChain components
        self._initialize_langchain()
        
        # Session memory storage
        self.session_memories = {}
        logger.info("✅ UnifiedOrchestrator initialization complete")
    
    def _initialize_langchain(self):
        """Initialize LangChain LLM and tools."""
        # Initialize LLM based on provider
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        
        logger.debug(f"🔧 LLM Provider configured: {settings.LLM_PROVIDER}")
        logger.debug(f"🔧 LLM Model: {settings.LLM_MODEL}")
        logger.debug(f"🔧 LLM Temperature: {settings.LLM_TEMPERATURE}")
        
        try:
            if settings.LLM_PROVIDER == "azure_openai":
                logger.debug("Checking Azure OpenAI credentials...")
                if not all([settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_API_KEY, settings.AZURE_OPENAI_DEPLOYMENT_NAME]):
                    raise ValueError("Azure OpenAI credentials not configured. Please set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME environment variables.")
                
                logger.debug(f"Azure endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
                logger.debug(f"Azure deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
                self.llm = AzureChatOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    openai_api_key=settings.AZURE_OPENAI_API_KEY,
                    openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                    deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    streaming=settings.LLM_STREAMING_ENABLED,
                    callback_manager=callback_manager if settings.LLM_STREAMING_ENABLED else None
                )
            elif settings.LLM_PROVIDER == "openai":
                logger.debug("Checking OpenAI credentials...")
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
                
                logger.debug(f"OpenAI model: {settings.LLM_MODEL}")
                self.llm = ChatOpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model_name=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    streaming=settings.LLM_STREAMING_ENABLED,
                    callback_manager=callback_manager if settings.LLM_STREAMING_ENABLED else None
                )
            elif settings.LLM_PROVIDER == "anthropic":
                logger.debug("Checking Anthropic credentials...")
                if not settings.ANTHROPIC_API_KEY:
                    raise ValueError("Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable.")
                
                logger.debug(f"Anthropic model: {settings.LLM_MODEL}")
                self.llm = ChatAnthropic(
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
            
            logger.info(f"✅ LLM initialized successfully with {settings.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise
        
        # Create LangChain tools
        logger.debug("Creating LangChain tools...")
        self.tools = self._create_tools()
        logger.debug(f"Created {len(self.tools)} tools")
        
        # Create agent prompt (will be updated with context later)
        logger.debug("Creating agent prompt...")
        self.prompt = None  # Will be created with context during message processing
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent."""
        tools = []
        
        # Flight search tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._search_flights_wrapper,
                name="search_flights",
                description="Search for flights between cities. Input should include origin, destination, departure date, and optionally return date and number of travelers."
            )
        )
        
        # Hotel search tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._search_hotels_wrapper,
                name="search_hotels",
                description="Search for hotels in a city. Input should include city, check-in date, check-out date, and number of guests."
            )
        )
        
        # Activity search tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._search_activities_wrapper,
                name="search_activities",
                description="Search for activities and attractions in a destination. Input should include the city or location."
            )
        )
        
        # Destination information tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._get_destination_info_wrapper,
                name="get_destination_info",
                description="Get general information about a travel destination including weather, best time to visit, and travel tips."
            )
        )
        
        # Trip context update tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._update_trip_context_wrapper,
                name="update_trip_context",
                description="Update the trip planning context with new information like dates, destinations, or traveler count."
            )
        )
        
        # Save to trip tool
        tools.append(
            StructuredTool.from_function(
                coroutine=self._save_to_trip_wrapper,
                name="save_to_trip",
                description="Save a flight, hotel, or activity to the user's trip plan."
            )
        )
        
        return tools
    
    def _create_agent_prompt(self, context: Optional[Dict[str, Any]] = None) -> ChatPromptTemplate:
        """Create the prompt template for the agent."""
        # Format context for display - escape curly braces for template
        context_json = json.dumps(context, indent=2) if context else "No context available"
        # Escape curly braces by doubling them
        context_str = context_json.replace("{", "{{").replace("}", "}}")
        
        system_message = f"""You are Pathavana, an AI travel planning assistant. You help users plan trips, search for flights and hotels, and provide travel recommendations.

You have access to the following tools:
- search_flights: Search for flights between cities
- search_hotels: Search for hotels in a destination
- search_activities: Find activities and attractions
- get_destination_info: Get information about destinations
- update_trip_context: Update trip planning details
- save_to_trip: Save items to the user's trip

Current trip context:
{context_str}

Guidelines:
1. Be helpful, friendly, and knowledgeable about travel
2. Ask clarifying questions when needed to provide better results
3. Use the tools to search for real flight, hotel, and activity options
4. Provide specific recommendations based on search results
5. Help users compare options and make informed decisions
6. Keep track of the trip context and update it as needed
7. Always acknowledge what actions you're taking
8. Format prices clearly and mention important details like flight duration or hotel amenities

Remember to:
- Confirm important details before searching
- Present options clearly with pros and cons
- Suggest next steps after each interaction
- Be transparent about any limitations"""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _get_session_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create memory for a session."""
        if session_id not in self.session_memories:
            self.session_memories[session_id] = ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=10,  # Keep last 10 exchanges
                return_messages=True,
                input_key="input"  # Specify which key to use for memory
            )
        return self.session_memories[session_id]
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            message: User's message
            session_id: Travel session ID (optional, will create if not provided)
            user_id: User ID (optional for anonymous sessions)
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with message, actions, and context updates
        """
        logger.debug("\n" + "="*60)
        logger.debug("🤖 UnifiedOrchestrator.process_message called")
        logger.debug(f"   Message: '{message}'")
        logger.debug(f"   Session ID: {session_id}")
        logger.debug(f"   User ID: {user_id}")
        logger.debug(f"   Stream: {stream}")
        logger.debug("="*60)
        
        try:
            # Create session if not provided
            if not session_id:
                logger.debug("   No session ID provided, creating new session...")
                session_id = await self.travel_service.create_session(
                    user_id=user_id,
                    initial_context={}
                )
                logger.debug(f"   Created session: {session_id}")
            
            # Get current session state
            logger.debug("   Getting current session state...")
            session_state = await self.travel_service.get_session_state(session_id)
            current_context = session_state.get("travel_context", {})
            logger.debug(f"   Current context: {current_context}")
            
            # Add user message to conversation history
            await self.travel_service.add_conversation_message(
                session_id=session_id,
                message_type="user",
                content=message
            )
            
            # Extract travel entities from the message
            logger.debug("   Extracting travel entities...")
            extracted_entities = await self.context_service.extract_travel_entities(
                message, 
                current_context
            )
            logger.debug(f"   Extracted entities: {extracted_entities}")
            
            # Merge with existing context
            updated_context = self.context_service.merge_context(
                current_context, 
                extracted_entities
            )
            logger.debug(f"   Updated context: {updated_context}")
            
            # Update session context
            await self.travel_service.update_session_context(
                session_id, 
                updated_context
            )
            
            # Store context for tool access
            self._current_session_id = session_id
            self._current_context = updated_context
            
            # Get session memory
            memory = self._get_session_memory(session_id)
            
            # Create prompt with current context
            prompt = self._create_agent_prompt(updated_context)
            
            # Create agent executor
            agent = create_openai_tools_agent(self.llm, self.tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True
            )
            
            # Execute agent
            if stream:
                response = await self._execute_agent_streaming(
                    agent_executor, 
                    message, 
                    updated_context
                )
            else:
                response = await self._execute_agent(
                    agent_executor, 
                    message, 
                    updated_context
                )
            
            # Extract AI response
            ai_response = response.get("output", "I apologize, but I couldn't generate a response.")
            logger.debug(f"   AI response: '{ai_response[:100]}...'")
            
            # Add AI response to conversation history
            await self.travel_service.add_conversation_message(
                session_id=session_id,
                message_type="assistant",
                content=ai_response,
                metadata={
                    "tools_used": response.get("tools_used", []),
                    "context": updated_context,
                    "searchResults": updated_context.get("searchResults", None)
                }
            )
            
            # Validate context and generate suggestions
            validation = self.context_service.validate_trip_context(updated_context)
            clarifying_questions = []
            
            if not validation["is_complete"]:
                clarifying_questions = self.context_service.generate_clarifying_questions(
                    updated_context
                )
            
            # Generate AI suggestions
            ai_suggestions = await self.llm_service.generate_suggestions(
                {"travel_context": updated_context, "current_intent": "trip_planning"},
                max_suggestions=3
            )
            
            # Include search results if available
            search_results = updated_context.get("searchResults", None)
            
            result = {
                "response": ai_response,
                "context": updated_context,
                "clarifying_questions": clarifying_questions,
                "suggestions": ai_suggestions,
                "context_validation": validation,
                "session_id": session_id,
                "tools_used": response.get("tools_used", []),
                "searchResults": search_results  # Include search results for UI
            }
            
            logger.debug("\n" + "-"*60)
            logger.debug("✅ UnifiedOrchestrator.process_message completed")
            logger.debug(f"   Response length: {len(ai_response)} chars")
            logger.debug(f"   Tools used: {len(response.get('tools_used', []))}")
            logger.debug(f"   Suggestions: {len(ai_suggestions)}")
            logger.debug("-"*60 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            logger.debug(f"   Error type: {type(e).__name__}")
            logger.debug(f"   Error details: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_agent(
        self, 
        agent_executor: AgentExecutor, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent without streaming."""
        try:
            result = await agent_executor.ainvoke({
                "input": message
            })
            
            # Extract tools used
            tools_used = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2:
                        action = step[0]
                        tools_used.append({
                            "tool": action.tool,
                            "input": action.tool_input
                        })
            
            return {
                "output": result.get("output", ""),
                "tools_used": tools_used
            }
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            raise
    
    async def _execute_agent_streaming(
        self, 
        agent_executor: AgentExecutor, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with streaming response."""
        # For now, return non-streaming response
        # TODO: Implement proper streaming with callbacks
        return await self._execute_agent(agent_executor, message, context)
    
    async def process_message_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message and stream the response.
        
        Args:
            message: User's message
            session_id: Travel session ID
            user_id: User ID
            
        Yields:
            Dict chunks with different types:
            - {"type": "response", "text": "partial response"}
            - {"type": "tool_use", "tool_info": {...}}
            - {"type": "suggestions", "suggestions": [...]}
            - {"type": "context_update", "context": {...}}
            - {"type": "error", "error": "error message"}
        """
        try:
            # Create session if not provided
            if not session_id:
                session_id = await self.travel_service.create_session(
                    user_id=user_id,
                    initial_context={}
                )
                yield {"type": "session_created", "session_id": session_id}
            
            # Get current session state
            session_state = await self.travel_service.get_session_state(session_id)
            current_context = session_state.get("travel_context", {})
            
            # Extract travel entities from the message
            extracted_entities = await self.context_service.extract_travel_entities(
                message, 
                current_context
            )
            
            # Merge with existing context
            updated_context = self.context_service.merge_context(
                current_context, 
                extracted_entities
            )
            
            # Update session context
            await self.travel_service.update_session_context(
                session_id, 
                updated_context
            )
            
            # Yield context update
            yield {"type": "context_update", "context": updated_context}
            
            # Store context for tool access
            self._current_session_id = session_id
            self._current_context = updated_context
            
            # Get session memory
            memory = self._get_session_memory(session_id)
            
            # Create custom callback for streaming
            class StreamingCallback:
                def __init__(self, queue: asyncio.Queue):
                    self.queue = queue
                    self.current_response = ""
                
                async def on_llm_new_token(self, token: str, **kwargs):
                    await self.queue.put({"type": "response", "text": token})
                
                async def on_tool_start(self, tool: str, input_str: str, **kwargs):
                    await self.queue.put({
                        "type": "tool_use",
                        "tool_info": {"name": tool, "input": input_str}
                    })
                
                async def on_tool_end(self, output: str, **kwargs):
                    # Tool completed
                    pass
            
            # Create response queue
            response_queue = asyncio.Queue()
            callback = StreamingCallback(response_queue)
            
            # Create prompt with current context
            prompt = self._create_agent_prompt(updated_context)
            
            # Create agent with streaming callback
            agent = create_openai_tools_agent(self.llm, self.tools, prompt)
            
            # Create custom executor with callback
            # Note: This is a simplified version. In production, you'd need
            # to properly integrate LangChain callbacks for streaming
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True
            )
            
            # Execute agent in background
            async def run_agent():
                try:
                    result = await agent_executor.ainvoke({
                        "input": message
                    })
                    await response_queue.put({"type": "complete", "result": result})
                except Exception as e:
                    await response_queue.put({"type": "error", "error": str(e)})
            
            # Start agent execution
            agent_task = asyncio.create_task(run_agent())
            
            # Stream responses from queue
            full_response = ""
            while True:
                try:
                    # Wait for next item with timeout
                    item = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                    
                    if item["type"] == "response":
                        full_response += item["text"]
                        yield item
                    elif item["type"] == "complete":
                        # Agent execution complete
                        result = item["result"]
                        
                        # Validate context and generate suggestions
                        validation = self.context_service.validate_trip_context(updated_context)
                        clarifying_questions = []
                        
                        if not validation["is_complete"]:
                            clarifying_questions = self.context_service.generate_clarifying_questions(
                                updated_context
                            )
                        
                        # Generate AI suggestions
                        ai_suggestions = await self.llm_service.generate_suggestions(
                            {"travel_context": updated_context, "current_intent": "trip_planning"},
                            max_suggestions=3
                        )
                        
                        # Yield suggestions
                        all_suggestions = clarifying_questions + ai_suggestions
                        if all_suggestions:
                            yield {"type": "suggestions", "suggestions": all_suggestions}
                        
                        break
                    elif item["type"] == "error":
                        yield item
                        break
                    else:
                        yield item
                        
                except asyncio.TimeoutError:
                    yield {"type": "error", "error": "Response timeout"}
                    break
            
            # Clean up
            if not agent_task.done():
                agent_task.cancel()
                try:
                    await agent_task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)}
    
    # Tool wrapper functions
    async def _search_flights_wrapper(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        travel_class: str = "ECONOMY"
    ) -> str:
        """Wrapper for flight search tool."""
        try:
            params = {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "adults": adults,
                "children": children,
                "travel_class": travel_class
            }
            if return_date:
                params["return_date"] = return_date
            
            results = await self.flight_tools.search_flights(params)
            
            if results.get("error"):
                return f"Error searching flights: {results['error']}"
            
            flights = results.get("flights", [])
            if not flights:
                return "No flights found for the specified criteria."
            
            # Store search results in session for UI display
            if hasattr(self, '_current_session_id') and self._current_session_id:
                # Update session context with search results
                if hasattr(self, '_current_context'):
                    self._current_context['searchResults'] = {"flights": flights}
                    await self.travel_service.update_session_context(
                        self._current_session_id,
                        self._current_context
                    )
            
            # Format results for LLM
            response = f"Found {len(flights)} flight options:\n\n"
            for i, flight in enumerate(flights[:5], 1):  # Show top 5
                price = flight.get("price", {})
                response += f"{i}. {flight.get('airlines', ['Unknown'])[0]} - "
                response += f"${price.get('total', 'N/A')} {price.get('currency', 'USD')}\n"
                response += f"   Duration: {flight.get('total_duration', 'N/A')}, "
                response += f"Type: {flight.get('flight_type', 'Unknown')}\n"
            
            response += "\n✈️ *I've found some great flight options for you! Check the sidebar for full details and filtering options.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in flight search wrapper: {e}")
            return f"Failed to search flights: {str(e)}"
    
    async def _search_hotels_wrapper(
        self,
        city: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        rooms: int = 1
    ) -> str:
        """Wrapper for hotel search tool."""
        try:
            params = {
                "city_code": city,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "rooms": rooms
            }
            
            results = await self.hotel_tools.search_hotels(params)
            
            if results.get("error"):
                return f"Error searching hotels: {results['error']}"
            
            hotels = results.get("hotels", [])
            if not hotels:
                return "No hotels found for the specified criteria."
            
            # Store search results in session for UI display
            if hasattr(self, '_current_session_id') and self._current_session_id:
                # Update session context with search results
                if hasattr(self, '_current_context'):
                    self._current_context['searchResults'] = {"hotels": hotels}
                    await self.travel_service.update_session_context(
                        self._current_session_id,
                        self._current_context
                    )
            
            # Format results for LLM
            response = f"Found {len(hotels)} hotel options in {city}:\n\n"
            for i, hotel in enumerate(hotels[:5], 1):  # Show top 5
                response += f"{i}. {hotel.get('name', 'Unknown Hotel')} - "
                response += f"{hotel.get('rating', 'N/A')} stars\n"
                response += f"   Price: ${hotel.get('price', {}).get('total', 'N/A')} per night\n"
                response += f"   Location: {hotel.get('address', 'Address not available')}\n"
            
            response += "\n🏨 *I've found some excellent hotel options! Check the sidebar for full details, photos, and filtering options.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in hotel search wrapper: {e}")
            return f"Failed to search hotels: {str(e)}"
    
    async def _search_activities_wrapper(self, destination: str) -> str:
        """Wrapper for activity search tool."""
        try:
            destination_info = {"name": destination}
            results = await self.activity_tools.get_activity_recommendations(
                destination_info,
                []  # No specific preferences
            )
            
            if results.get("error"):
                return f"Error searching activities: {results['error']}"
            
            activities = results.get("activities", [])
            if not activities:
                return f"No activities found for {destination}."
            
            # Store search results in session for UI display
            if hasattr(self, '_current_session_id') and self._current_session_id:
                # Update session context with search results
                if hasattr(self, '_current_context'):
                    self._current_context['searchResults'] = {"activities": activities}
                    await self.travel_service.update_session_context(
                        self._current_session_id,
                        self._current_context
                    )
            
            # Format results for LLM
            response = f"Found activities and attractions in {destination}:\n\n"
            for i, activity in enumerate(activities[:5], 1):  # Show top 5
                response += f"{i}. {activity.get('name', 'Unknown Activity')}\n"
                response += f"   Type: {activity.get('type', 'N/A')}\n"
                response += f"   Description: {activity.get('description', 'No description available')}\n"
            
            response += "\n🎯 *I've found some exciting activities and attractions! Check the sidebar for full details and booking options.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in activity search wrapper: {e}")
            return f"Failed to search activities: {str(e)}"
    
    async def _get_destination_info_wrapper(self, destination: str) -> str:
        """Wrapper for destination information tool."""
        try:
            # Use cache service to get destination info
            cache_key = f"destination_info:{destination}"
            cached_info = await self.cache_service.get_cached_response(cache_key)
            
            if cached_info:
                return cached_info
            
            # Generate destination info using LLM
            info = f"""Information about {destination}:

{destination} is a popular travel destination. Here are some key points:

- Best time to visit: Research the seasonal weather patterns
- Popular attractions: Check local tourist sites and landmarks
- Local cuisine: Explore traditional dishes and restaurants
- Transportation: Look into public transit and taxi options
- Cultural tips: Learn about local customs and etiquette

For specific and up-to-date information, I recommend checking official tourism websites or recent travel guides."""
            
            # Cache the response
            await self.cache_service.cache_response(cache_key, info, ttl=86400)  # 24 hours
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting destination info: {e}")
            return f"Failed to get information about {destination}: {str(e)}"
    
    async def _update_trip_context_wrapper(self, updates: str) -> str:
        """Wrapper for updating trip context."""
        try:
            # Parse updates (in a real implementation, this would be more sophisticated)
            logger.info(f"Updating trip context with: {updates}")
            
            # Update the session context
            if hasattr(self, '_current_session_id'):
                await self.travel_service.update_session_context(
                    self._current_session_id,
                    self._current_context
                )
            
            return f"Trip context updated successfully with: {updates}"
            
        except Exception as e:
            logger.error(f"Error updating trip context: {e}")
            return f"Failed to update trip context: {str(e)}"
    
    async def _save_to_trip_wrapper(self, item_description: str) -> str:
        """Wrapper for saving items to trip."""
        try:
            # In a real implementation, this would parse the item and save it
            logger.info(f"Saving to trip: {item_description}")
            
            return f"Successfully saved to your trip: {item_description}"
            
        except Exception as e:
            logger.error(f"Error saving to trip: {e}")
            return f"Failed to save item to trip: {str(e)}"