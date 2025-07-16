"""
LLM service for AI/language model integration.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from abc import ABC, abstractmethod
import openai
from openai import AzureOpenAI, AsyncAzureOpenAI
import anthropic
import json
import logging
from datetime import datetime
import asyncio
from functools import lru_cache

from ..core.config import settings
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Base class for LLM service implementations."""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM."""
        pass


class AzureOpenAIService(BaseLLMService):
    """Azure OpenAI service implementation."""
    
    def __init__(self):
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI API key not configured")
        if not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI endpoint not configured")
        
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION or "2024-02-01",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4"
        self.model = settings.LLM_MODEL
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a response from Azure OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=kwargs.get("temperature", temperature),
                max_tokens=kwargs.get("max_tokens", max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            raise
    
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from Azure OpenAI."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Azure OpenAI streaming error: {e}")
            raise


class OpenAIService(BaseLLMService):
    """OpenAI GPT service implementation."""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response using OpenAI GPT."""
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name if isinstance(self, AzureOpenAIService) else self.model,
                messages=messages,
                temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                top_p=kwargs.get("top_p", 0.95),
                frequency_penalty=kwargs.get("frequency_penalty", 0),
                presence_penalty=kwargs.get("presence_penalty", 0)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using OpenAI GPT."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment_name if isinstance(self, AzureOpenAIService) else self.model,
                messages=messages,
                temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                top_p=kwargs.get("top_p", 0.95),
                frequency_penalty=kwargs.get("frequency_penalty", 0),
                presence_penalty=kwargs.get("presence_penalty", 0),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")


class AnthropicService(BaseLLMService):
    """Anthropic Claude service implementation."""
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured")
        
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response using Anthropic Claude."""
        try:
            # Convert OpenAI-style messages to Anthropic format
            anthropic_messages = self._convert_messages(messages)
            
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS)
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using Anthropic Claude."""
        try:
            anthropic_messages = self._convert_messages(messages)
            
            async with self.client.messages.stream(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS)
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert OpenAI-style messages to Anthropic format."""
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                # Anthropic handles system messages differently
                continue
            converted.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })
        return converted


class LLMService:
    """Main LLM service that delegates to specific implementations with fallback support."""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.cache_service = CacheService()
        self.primary_service = None
        self.fallback_service = None
        
        # Initialize primary service
        if self.provider == "azure_openai":
            try:
                self.primary_service = AzureOpenAIService()
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI: {e}")
        elif self.provider == "openai":
            try:
                self.primary_service = OpenAIService()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        elif self.provider == "anthropic":
            try:
                self.primary_service = AnthropicService()
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
        
        # Initialize fallback service
        if not self.primary_service:
            raise ValueError(f"Failed to initialize primary LLM provider: {self.provider}")
        
        # Setup fallback (Anthropic Claude as fallback)
        if self.provider != "anthropic" and settings.ANTHROPIC_API_KEY:
            try:
                self.fallback_service = AnthropicService()
                logger.info("Fallback LLM service (Anthropic) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback service: {e}")
    
    @property
    def service(self) -> BaseLLMService:
        """Get the current active service."""
        return self.primary_service
    
    async def generate_travel_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        travel_context: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Generate a travel-focused response considering context and history.
        """
        # Build messages for the LLM
        messages = self._build_travel_messages(
            user_message, 
            conversation_history, 
            travel_context
        )
        
        return await self.service.generate_response(messages, **kwargs)
    
    async def stream_travel_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        travel_context: Dict[str, Any],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a travel-focused response.
        """
        messages = self._build_travel_messages(
            user_message, 
            conversation_history, 
            travel_context
        )
        
        async for chunk in self.service.stream_response(messages, **kwargs):
            yield chunk
    
    async def parse_travel_query_to_json(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse travel query to structured JSON format.
        """
        system_prompt = self._build_travel_parsing_prompt()
        context_str = json.dumps(context, indent=2) if context else "No previous context"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context_str}\n\nQuery: {query}"}
        ]
        
        try:
            response = await self._generate_with_fallback(
                messages,
                temperature=0.1,
                max_tokens=800
            )
            
            parsed_data = self._parse_json_response(response)
            return self._validate_travel_data(parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing travel query: {e}")
            return {
                "error": str(e),
                "raw_query": query
            }
    
    async def generate_suggestions(
        self,
        session_data: Dict[str, Any],
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Generate contextual suggestions for the user.
        """
        # Check cache
        cache_key = f"suggestions:{str(session_data)[:200]}"
        cached_suggestions = await self.cache_service.get_cached_response(cache_key)
        if cached_suggestions:
            return cached_suggestions[:max_suggestions]
        
        prompt = self._build_suggestion_prompt(session_data)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate helpful suggestions based on the current context."}
        ]
        
        try:
            response = await self._generate_with_fallback(
                messages,
                temperature=0.8,
                max_tokens=300
            )
            
            suggestions = self._extract_suggestions(response)
            
            # Cache suggestions
            await self.cache_service.cache_response(cache_key, suggestions)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._get_default_suggestions(session_data)
    
    async def resolve_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflicts in travel data using AI.
        """
        prompt = self._build_conflict_resolution_prompt(conflicts, context)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Resolve these conflicts based on the conversation context."}
        ]
        
        try:
            response = await self._generate_with_fallback(
                messages,
                temperature=0.3,
                max_tokens=500
            )
            
            resolution = self._parse_json_response(response)
            return {
                "resolved": True,
                "resolution": resolution,
                "confidence": resolution.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            return {
                "resolved": False,
                "error": str(e)
            }
    
    async def format_response_for_chat(
        self,
        data: Dict[str, Any],
        response_type: str
    ) -> str:
        """
        Format structured data into natural language for chat.
        """
        prompt = self._build_formatting_prompt(data, response_type)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Format this data conversationally."}
        ]
        
        try:
            response = await self._generate_with_fallback(
                messages,
                temperature=0.7,
                max_tokens=600
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return self._fallback_format(data, response_type)
    
    async def _generate_with_fallback(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate response with fallback to secondary service.
        """
        try:
            # Try primary service first
            response = await self.primary_service.generate_response(messages, **kwargs)
            return response
            
        except Exception as e:
            logger.warning(f"Primary LLM service failed: {e}")
            
            # Try fallback service if available
            if self.fallback_service:
                try:
                    logger.info("Using fallback LLM service")
                    response = await self.fallback_service.generate_response(messages, **kwargs)
                    return response
                except Exception as fallback_e:
                    logger.error(f"Fallback LLM service also failed: {fallback_e}")
            
            raise Exception("All LLM services failed")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Safely parse JSON from LLM response.
        """
        # Try to extract JSON from the response
        response = response.strip()
        
        # Handle code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        # Try to parse
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            raise e
    
    def _validate_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance intent data.
        """
        valid_intents = [
            "flight_search", "hotel_search", "activity_search",
            "trip_planning", "booking_assistance", "general_travel_info",
            "destination_info", "itinerary_management", "other"
        ]
        
        # Ensure required fields
        validated = {
            "intent": intent_data.get("intent", "other"),
            "entities": intent_data.get("entities", {}),
            "confidence": float(intent_data.get("confidence", 0.5))
        }
        
        # Validate intent
        if validated["intent"] not in valid_intents:
            validated["intent"] = "other"
            validated["confidence"] *= 0.8
        
        # Ensure confidence is in valid range
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))
        
        return validated
    
    def _validate_travel_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsed travel data.
        """
        validated = data.copy()
        
        # Ensure core fields exist
        if "destinations" not in validated:
            validated["destinations"] = []
        if "dates" not in validated:
            validated["dates"] = {}
        if "travelers" not in validated:
            validated["travelers"] = {"adults": 1}
        
        return validated
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """
        Extract suggestion list from LLM response.
        """
        suggestions = []
        
        # Try to parse as list
        try:
            data = self._parse_json_response(response)
            if isinstance(data, list):
                suggestions = data
            elif isinstance(data, dict) and "suggestions" in data:
                suggestions = data["suggestions"]
        except:
            # Fallback to line-based extraction
            lines = response.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove common prefixes
                    for prefix in ["- ", "* ", "1. ", "2. ", "3. "]:
                        if line.startswith(prefix):
                            line = line[len(prefix):]
                            break
                    if line:
                        suggestions.append(line)
        
        return suggestions
    
    def _get_default_suggestions(self, session_data: Dict[str, Any]) -> List[str]:
        """
        Get default suggestions based on session state.
        """
        suggestions = []
        
        context = session_data.get("travel_context", {})
        
        if not context.get("destinations"):
            suggestions.append("Where would you like to travel?")
        elif not context.get("dates"):
            suggestions.append("When are you planning to travel?")
        elif not context.get("travelers"):
            suggestions.append("How many people will be traveling?")
        else:
            suggestions.extend([
                "Would you like to search for flights?",
                "Are you looking for hotel recommendations?",
                "What activities interest you at your destination?"
            ])
        
        return suggestions[:3]
    
    def _fallback_format(self, data: Dict[str, Any], response_type: str) -> str:
        """
        Fallback formatting when LLM fails.
        """
        if response_type == "flight_results":
            return f"I found {len(data.get('flights', []))} flight options for your search."
        elif response_type == "hotel_results":
            return f"I found {len(data.get('hotels', []))} hotel options in your destination."
        elif response_type == "activity_results":
            return f"Here are {len(data.get('activities', []))} activities you might enjoy."
        else:
            return "Here's what I found based on your request."
    
    async def extract_travel_intent(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract travel intent and entities from user message with caching.
        """
        # Check cache first
        cache_key = f"intent:{user_message[:100]}:{str(context)[:100]}"
        cached_intent = await self.cache_service.get_cached_response(
            cache_key, 
            ttl=3600  # 1 hour cache
        )
        if cached_intent:
            logger.info("Using cached intent extraction")
            return cached_intent
        
        intent_prompt = self._build_intent_extraction_prompt(user_message, context)
        messages = [
            {"role": "system", "content": intent_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self._generate_with_fallback(
                messages, 
                temperature=0.1,  # Lower temperature for more consistent intent extraction
                max_tokens=500
            )
            
            # Parse JSON response
            intent_data = self._parse_json_response(response)
            
            # Validate and enhance intent data
            validated_intent = self._validate_intent(intent_data)
            
            # Cache the result
            await self.cache_service.cache_response(cache_key, validated_intent)
            
            return validated_intent
            
        except Exception as e:
            logger.error(f"Error extracting intent: {e}")
            # Fallback if extraction fails
            return {
                "intent": "general_travel_assistance",
                "entities": {},
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _build_travel_messages(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        travel_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Build message array for travel conversation."""
        system_prompt = self._get_travel_system_prompt(travel_context)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg.get("type", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _get_travel_system_prompt(self, travel_context: Dict[str, Any]) -> str:
        """Get the system prompt for travel conversations."""
        context_info = json.dumps(travel_context, indent=2) if travel_context else "No context available"
        
        return f"""You are Pathavana, an AI travel planning assistant. You help users plan trips, search for flights and hotels, and provide travel recommendations.

Current Travel Context:
{context_info}

Guidelines:
1. Be helpful, friendly, and knowledgeable about travel
2. Ask clarifying questions when needed
3. Provide specific recommendations when possible
4. Consider the user's context and preferences
5. If you need to search for flights, hotels, or activities, let the user know
6. Always prioritize user safety and provide accurate information
7. If you don't have real-time data, be transparent about limitations

Respond naturally and conversationally while being informative and helpful.

IMPORTANT: 
- Always acknowledge the user's request
- Be specific about what actions you're taking or have taken
- If you've searched for something, share key findings
- Ask clarifying questions when needed
- Keep responses concise but informative"""
    
    def _build_intent_extraction_prompt(
        self, 
        user_message: str, 
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for intent extraction."""
        return """You are an intent extraction system for a travel planning application. 
Analyze the user's message and extract:

1. Primary intent (one of: flight_search, hotel_search, activity_search, trip_planning, booking_assistance, general_travel_info, other)
2. Entities mentioned (destinations, dates, passenger count, preferences, etc.)
3. Confidence score (0.0 to 1.0)

Return ONLY a JSON object with this structure:
{
    "intent": "intent_name",
    "entities": {
        "destination": "location",
        "departure_location": "location", 
        "dates": {"departure": "date", "return": "date"},
        "passengers": "number",
        "preferences": ["list", "of", "preferences"]
    },
    "confidence": 0.8
}

Include only entities that are clearly mentioned or implied in the message.

Do not include explanations or additional text - return ONLY the JSON object."""
    
    def _build_travel_parsing_prompt(self) -> str:
        """Build prompt for parsing travel queries."""
        return """You are a travel query parser. Extract travel information and return it as JSON.  

Parse the following information:
- Destinations (cities, countries, regions)
- Dates (departure, return, flexibility)
- Number and type of travelers
- Budget information
- Preferences (direct flights, hotel stars, activities)
- Trip purpose (business, leisure, etc.)

Return a JSON object with this structure:
{
    "destinations": [{"name": "string", "type": "city|country|region"}],
    "dates": {
        "departure": "YYYY-MM-DD or descriptive",
        "return": "YYYY-MM-DD or descriptive", 
        "flexible": boolean
    },
    "travelers": {
        "adults": number,
        "children": number,
        "infants": number
    },
    "budget": {
        "amount": number,
        "currency": "string",
        "per_person": boolean
    },
    "preferences": ["list of preferences"],
    "trip_type": "leisure|business|mixed"
}

If information is not provided, omit that field. Return ONLY valid JSON."""
    
    def _build_suggestion_prompt(self, session_data: Dict[str, Any]) -> str:
        """Build prompt for generating suggestions."""
        context = session_data.get("travel_context", {})
        intent = session_data.get("current_intent", "unknown")
        
        return f"""You are a helpful travel planning assistant. Based on the current conversation context, generate 3-5 relevant suggestions or questions to help the user plan their trip.

Current Context:
- Intent: {intent}
- Destinations: {context.get('destinations', 'Not specified')}
- Dates: {context.get('dates', 'Not specified')}
- Travelers: {context.get('travelers', 'Not specified')}
- Preferences: {context.get('preferences', 'None stated')}

Generate suggestions that:
1. Help clarify missing information
2. Offer relevant travel tips or options
3. Move the conversation forward productively

Return suggestions as a JSON array of strings."""
    
    def _build_conflict_resolution_prompt(self, conflicts: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """Build prompt for conflict resolution."""
        return f"""You are resolving conflicts in travel planning data. The user has provided conflicting information:

Conflicts:
{json.dumps(conflicts, indent=2)}

Conversation Context:
{json.dumps(context, indent=2)}

Resolve these conflicts by:
1. Analyzing the conversation history to understand user intent
2. Choosing the most recent or most specific information
3. Considering the overall trip context

Return a JSON object with:
{{
    "resolutions": {{
        "field_name": "resolved_value"
    }},
    "reasoning": "Brief explanation of resolution logic",
    "confidence": 0.0-1.0
}}"""
    
    def _build_formatting_prompt(self, data: Dict[str, Any], response_type: str) -> str:
        """Build prompt for formatting responses."""
        type_prompts = {
            "flight_results": "Format these flight search results in a conversational way. Highlight: cheapest option, fastest option, and best overall value. Mention key details like airlines, duration, and stops.",
            "hotel_results": "Format these hotel results conversationally. Mention: top-rated options, best value, and unique features. Include location, price range, and amenities.",
            "activity_results": "Present these activities in an engaging way. Group by type if applicable, highlight must-see attractions, and mention prices/duration.",
            "booking_confirmation": "Confirm the booking details in a friendly, reassuring way. Summarize what was booked and next steps.",
            "error": "Explain this error in a helpful, non-technical way and suggest what the user can do."
        }
        
        prompt = type_prompts.get(response_type, "Format this information in a clear, conversational way.")
        
        return f"""{prompt}

Data to format:
{json.dumps(data, indent=2)}

Guidelines:
- Be conversational but informative
- Use natural language, not technical jargon  
- Keep it concise but include important details
- End with a question or suggestion for next steps"""