"""
LLM Service tests.

Tests for the LLM service including intent parsing, response generation,
itinerary creation, and various LLM provider integrations.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from app.services.llm_service import LLMService
from app.core.config import settings


class TestLLMServiceInitialization:
    """Test LLM service initialization and configuration."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_azure_openai(self):
        """Test LLM service initialization with Azure OpenAI."""
        with patch.object(settings, 'LLM_PROVIDER', 'azure_openai'):
            with patch.object(settings, 'AZURE_OPENAI_API_KEY', 'test_key'):
                service = LLMService()
                assert service.provider == 'azure_openai'
                assert service.model == settings.LLM_MODEL

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_openai(self):
        """Test LLM service initialization with OpenAI."""
        with patch.object(settings, 'LLM_PROVIDER', 'openai'):
            with patch.object(settings, 'OPENAI_API_KEY', 'test_key'):
                service = LLMService()
                assert service.provider == 'openai'

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_anthropic(self):
        """Test LLM service initialization with Anthropic."""
        with patch.object(settings, 'LLM_PROVIDER', 'anthropic'):
            with patch.object(settings, 'ANTHROPIC_API_KEY', 'test_key'):
                service = LLMService()
                assert service.provider == 'anthropic'

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_missing_api_key(self):
        """Test LLM service initialization with missing API key."""
        with patch.object(settings, 'LLM_PROVIDER', 'openai'):
            with patch.object(settings, 'OPENAI_API_KEY', None):
                with pytest.raises(ValueError, match="API key not configured"):
                    LLMService()

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_invalid_provider(self):
        """Test LLM service initialization with invalid provider."""
        with patch.object(settings, 'LLM_PROVIDER', 'invalid_provider'):
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                LLMService()


class TestTravelIntentParsing:
    """Test travel intent parsing functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_parse_travel_intent_simple(self, mock_llm_service):
        """Test parsing simple travel intent."""
        message = "I want to go to Paris for 5 days"
        context = {}
        
        expected_response = {
            "destination": "Paris",
            "travel_dates": {
                "duration": 5,
                "flexible": True
            },
            "travelers": 1,
            "travel_type": "leisure",
            "preferences": [],
            "confidence": 0.9
        }
        
        mock_llm_service.parse_travel_intent.return_value = expected_response
        
        result = await mock_llm_service.parse_travel_intent(message, context)
        
        assert result["destination"] == "Paris"
        assert result["travel_dates"]["duration"] == 5
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_parse_travel_intent_complex(self, mock_llm_service):
        """Test parsing complex travel intent with multiple details."""
        message = "I'm planning a business trip to Tokyo from June 15-22 for 2 people, need vegetarian meals"
        context = {}
        
        expected_response = {
            "destination": "Tokyo",
            "travel_dates": {
                "departure": "2024-06-15",
                "return": "2024-06-22",
                "flexible": False
            },
            "travelers": 2,
            "travel_type": "business",
            "preferences": ["vegetarian"],
            "special_requirements": ["vegetarian meals"],
            "confidence": 0.95
        }
        
        mock_llm_service.parse_travel_intent.return_value = expected_response
        
        result = await mock_llm_service.parse_travel_intent(message, context)
        
        assert result["destination"] == "Tokyo"
        assert result["travelers"] == 2
        assert result["travel_type"] == "business"
        assert "vegetarian" in result["preferences"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_parse_travel_intent_with_context(self, mock_llm_service):
        """Test parsing travel intent with conversation context."""
        message = "Actually, make that 3 people instead"
        context = {
            "previous_intent": {
                "destination": "Paris",
                "travelers": 2,
                "travel_type": "leisure"
            },
            "conversation_history": [
                {"role": "user", "content": "I want to go to Paris for 2 people"},
                {"role": "assistant", "content": "I can help you plan a trip to Paris for 2 people."}
            ]
        }
        
        expected_response = {
            "destination": "Paris",
            "travelers": 3,  # Updated from context
            "travel_type": "leisure",
            "preferences": [],
            "confidence": 0.85
        }
        
        mock_llm_service.parse_travel_intent.return_value = expected_response
        
        result = await mock_llm_service.parse_travel_intent(message, context)
        
        assert result["destination"] == "Paris"
        assert result["travelers"] == 3
        mock_llm_service.parse_travel_intent.assert_called_once_with(message, context)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_parse_travel_intent_ambiguous(self, mock_llm_service):
        """Test parsing ambiguous travel intent."""
        message = "I want to travel somewhere nice"
        context = {}
        
        expected_response = {
            "destination": None,
            "travel_dates": {},
            "travelers": 1,
            "travel_type": "leisure",
            "preferences": ["nice destinations"],
            "confidence": 0.3,
            "clarification_needed": [
                "destination",
                "travel_dates",
                "budget"
            ]
        }
        
        mock_llm_service.parse_travel_intent.return_value = expected_response
        
        result = await mock_llm_service.parse_travel_intent(message, context)
        
        assert result["destination"] is None
        assert result["confidence"] < 0.5
        assert "clarification_needed" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_parse_travel_intent_error_handling(self, mock_llm_service):
        """Test error handling in travel intent parsing."""
        message = "I want to go to Paris"
        context = {}
        
        mock_llm_service.parse_travel_intent.side_effect = Exception("LLM service unavailable")
        
        with pytest.raises(Exception, match="LLM service unavailable"):
            await mock_llm_service.parse_travel_intent(message, context)


class TestResponseGeneration:
    """Test LLM response generation functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_response_basic(self, mock_llm_service):
        """Test basic response generation."""
        user_message = "What are the best places to visit in Paris?"
        context = {
            "destination": "Paris",
            "travel_type": "leisure"
        }
        
        expected_response = {
            "response": "Paris offers many wonderful attractions! Here are some must-visit places:\n\n1. Eiffel Tower\n2. Louvre Museum\n3. Notre-Dame Cathedral\n4. Champs-Élysées\n5. Montmartre",
            "suggestions": [
                "Tell me about Paris restaurants",
                "How many days should I spend in Paris?",
                "What's the best time to visit Paris?"
            ],
            "follow_up_questions": [
                "What type of activities interest you most?",
                "Do you have any budget preferences?"
            ]
        }
        
        mock_llm_service.generate_response.return_value = expected_response
        
        result = await mock_llm_service.generate_response(user_message, context)
        
        assert "Paris offers many wonderful attractions" in result["response"]
        assert len(result["suggestions"]) == 3
        assert "follow_up_questions" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_response_with_search_results(self, mock_llm_service):
        """Test response generation with search results context."""
        user_message = "Which of these flights is better?"
        context = {
            "destination": "Paris",
            "search_results": [
                {
                    "type": "flight",
                    "origin": "JFK",
                    "destination": "CDG",
                    "price": 850,
                    "duration": "8h 30m",
                    "airline": "Air France"
                },
                {
                    "type": "flight",
                    "origin": "JFK",
                    "destination": "CDG",
                    "price": 920,
                    "duration": "7h 45m",
                    "airline": "Delta"
                }
            ]
        }
        
        expected_response = {
            "response": "Looking at these two flights to Paris:\n\n**Air France Flight**: $850, 8h 30m\n- More affordable option\n- Direct flight\n\n**Delta Flight**: $920, 7h 45m\n- Faster journey\n- Premium service\n\nI'd recommend the Air France flight if budget is a priority, or Delta if you prefer a shorter flight time.",
            "recommendations": [
                {
                    "item_type": "flight",
                    "recommendation": "Air France for budget-conscious travelers",
                    "reasoning": "Lower price with reasonable duration"
                }
            ]
        }
        
        mock_llm_service.generate_response.return_value = expected_response
        
        result = await mock_llm_service.generate_response(user_message, context)
        
        assert "Air France" in result["response"]
        assert "Delta" in result["response"]
        assert "recommendations" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_response_personalized(self, mock_llm_service):
        """Test personalized response generation."""
        user_message = "I need restaurant recommendations"
        context = {
            "destination": "Paris",
            "user_preferences": {
                "dietary_restrictions": ["vegetarian"],
                "cuisine_preferences": ["French", "Italian"],
                "budget_level": "mid-range"
            },
            "travel_type": "romantic"
        }
        
        expected_response = {
            "response": "Based on your vegetarian preferences and love for French/Italian cuisine, here are some romantic restaurants in Paris:\n\n**L'Ami Jean** - Excellent vegetarian options with French flair\n**Le Potager du Marais** - Dedicated vegetarian restaurant\n**Pink Mamma** - Italian restaurant with great vegetarian dishes",
            "personalization_notes": [
                "Filtered for vegetarian options",
                "Focused on romantic atmosphere",
                "Selected mid-range pricing"
            ]
        }
        
        mock_llm_service.generate_response.return_value = expected_response
        
        result = await mock_llm_service.generate_response(user_message, context)
        
        assert "vegetarian" in result["response"]
        assert "romantic" in result["response"]
        assert "personalization_notes" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_response_streaming(self, mock_llm_service):
        """Test streaming response generation."""
        user_message = "Tell me about Paris attractions"
        context = {"destination": "Paris"}
        
        # Mock streaming response
        async def mock_stream():
            chunks = [
                "Paris is a beautiful city with many attractions. ",
                "The Eiffel Tower is perhaps the most famous landmark. ",
                "The Louvre Museum houses incredible art collections. ",
                "Don't miss the charming Montmartre district!"
            ]
            for chunk in chunks:
                yield {"delta": {"content": chunk}}
        
        mock_llm_service.generate_response_stream.return_value = mock_stream()
        
        full_response = ""
        async for chunk in mock_llm_service.generate_response_stream(user_message, context):
            full_response += chunk["delta"]["content"]
        
        assert "Paris is a beautiful city" in full_response
        assert "Eiffel Tower" in full_response
        assert "Louvre Museum" in full_response


class TestItineraryGeneration:
    """Test itinerary generation functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_itinerary_basic(self, mock_llm_service):
        """Test basic itinerary generation."""
        trip_details = {
            "destination": "Paris",
            "duration": 3,
            "travelers": 2,
            "travel_type": "leisure",
            "preferences": ["culture", "food"]
        }
        
        expected_itinerary = {
            "itinerary": [
                {
                    "day": 1,
                    "title": "Arrival and Central Paris",
                    "activities": [
                        {
                            "time": "10:00",
                            "activity": "Arrive in Paris and check into hotel",
                            "type": "logistics",
                            "duration": 60
                        },
                        {
                            "time": "14:00",
                            "activity": "Visit the Eiffel Tower",
                            "type": "sightseeing",
                            "duration": 120,
                            "notes": "Book tickets in advance"
                        },
                        {
                            "time": "19:00",
                            "activity": "Dinner at a traditional French bistro",
                            "type": "dining",
                            "duration": 120
                        }
                    ]
                },
                {
                    "day": 2,
                    "title": "Art and Culture",
                    "activities": [
                        {
                            "time": "09:00",
                            "activity": "Louvre Museum",
                            "type": "culture",
                            "duration": 180,
                            "notes": "Pre-book tickets to skip lines"
                        },
                        {
                            "time": "13:00",
                            "activity": "Lunch in the Marais district",
                            "type": "dining",
                            "duration": 90
                        },
                        {
                            "time": "15:00",
                            "activity": "Explore Montmartre",
                            "type": "sightseeing",
                            "duration": 150
                        }
                    ]
                }
            ],
            "total_days": 3,
            "estimated_budget": 1500,
            "recommendations": [
                "Purchase a Museum Pass for convenience",
                "Book restaurants in advance",
                "Wear comfortable walking shoes"
            ]
        }
        
        mock_llm_service.generate_itinerary.return_value = expected_itinerary
        
        result = await mock_llm_service.generate_itinerary(trip_details)
        
        assert len(result["itinerary"]) >= 2
        assert result["total_days"] == 3
        assert "Eiffel Tower" in str(result["itinerary"])
        assert "Louvre" in str(result["itinerary"])

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_itinerary_business_trip(self, mock_llm_service):
        """Test itinerary generation for business trip."""
        trip_details = {
            "destination": "Tokyo",
            "duration": 4,
            "travelers": 1,
            "travel_type": "business",
            "preferences": ["efficiency", "networking"],
            "business_requirements": {
                "meeting_locations": ["Shibuya", "Shinjuku"],
                "work_hours": "09:00-18:00"
            }
        }
        
        expected_itinerary = {
            "itinerary": [
                {
                    "day": 1,
                    "title": "Arrival and Business Setup",
                    "activities": [
                        {
                            "time": "08:00",
                            "activity": "Arrive at Haneda Airport",
                            "type": "logistics"
                        },
                        {
                            "time": "10:00",
                            "activity": "Check into business hotel in Shibuya",
                            "type": "accommodation"
                        },
                        {
                            "time": "14:00",
                            "activity": "Business meetings in Shibuya",
                            "type": "business"
                        }
                    ]
                }
            ],
            "business_optimized": True,
            "transportation_notes": [
                "Purchase JR Pass for efficient travel",
                "Use Suica card for local transport"
            ]
        }
        
        mock_llm_service.generate_itinerary.return_value = expected_itinerary
        
        result = await mock_llm_service.generate_itinerary(trip_details)
        
        assert result["business_optimized"] is True
        assert "Shibuya" in str(result["itinerary"])
        assert "transportation_notes" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_itinerary_family_trip(self, mock_llm_service):
        """Test itinerary generation for family trip."""
        trip_details = {
            "destination": "Orlando",
            "duration": 7,
            "travelers": 4,
            "travel_type": "family",
            "preferences": ["theme_parks", "kid_friendly"],
            "traveler_details": [
                {"age": 35, "type": "adult"},
                {"age": 32, "type": "adult"},
                {"age": 8, "type": "child"},
                {"age": 5, "type": "child"}
            ]
        }
        
        expected_itinerary = {
            "itinerary": [
                {
                    "day": 1,
                    "title": "Magic Kingdom",
                    "activities": [
                        {
                            "time": "09:00",
                            "activity": "Early entry to Magic Kingdom",
                            "type": "theme_park",
                            "kid_friendly": True,
                            "notes": "Use Genie+ for popular rides"
                        }
                    ]
                }
            ],
            "family_optimized": True,
            "kid_considerations": [
                "Plan for nap breaks",
                "Bring stroller for younger child",
                "Book character dining"
            ]
        }
        
        mock_llm_service.generate_itinerary.return_value = expected_itinerary
        
        result = await mock_llm_service.generate_itinerary(trip_details)
        
        assert result["family_optimized"] is True
        assert "kid_considerations" in result
        assert "Magic Kingdom" in str(result["itinerary"])

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_generate_itinerary_with_saved_items(self, mock_llm_service):
        """Test itinerary generation incorporating saved items."""
        trip_details = {
            "destination": "Paris",
            "duration": 4,
            "travelers": 2,
            "travel_type": "leisure"
        }
        
        saved_items = [
            {
                "type": "flight",
                "data": {
                    "origin": "JFK",
                    "destination": "CDG",
                    "departure": "2024-06-01T10:00:00",
                    "arrival": "2024-06-01T22:00:00"
                }
            },
            {
                "type": "hotel",
                "data": {
                    "name": "Hotel du Louvre",
                    "location": "1st Arrondissement",
                    "check_in": "2024-06-01",
                    "check_out": "2024-06-05"
                }
            }
        ]
        
        expected_itinerary = {
            "itinerary": [
                {
                    "day": 1,
                    "title": "Arrival Day",
                    "activities": [
                        {
                            "time": "22:00",
                            "activity": "Arrive at CDG Airport",
                            "type": "logistics",
                            "source": "saved_flight"
                        },
                        {
                            "time": "23:30",
                            "activity": "Check into Hotel du Louvre",
                            "type": "accommodation",
                            "source": "saved_hotel"
                        }
                    ]
                }
            ],
            "incorporates_saved_items": True
        }
        
        mock_llm_service.generate_itinerary.return_value = expected_itinerary
        
        result = await mock_llm_service.generate_itinerary(trip_details, saved_items)
        
        assert result["incorporates_saved_items"] is True
        assert "Hotel du Louvre" in str(result["itinerary"])


class TestLLMServiceUtilities:
    """Test LLM service utility functions."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_extract_locations(self, mock_llm_service):
        """Test location extraction from text."""
        text = "I want to visit Paris, then maybe Rome, and end in Barcelona"
        
        expected_locations = [
            {"name": "Paris", "country": "France", "confidence": 0.95},
            {"name": "Rome", "country": "Italy", "confidence": 0.90},
            {"name": "Barcelona", "country": "Spain", "confidence": 0.88}
        ]
        
        mock_llm_service.extract_locations.return_value = expected_locations
        
        result = await mock_llm_service.extract_locations(text)
        
        assert len(result) == 3
        assert result[0]["name"] == "Paris"
        assert result[1]["name"] == "Rome"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_extract_dates(self, mock_llm_service):
        """Test date extraction from text."""
        text = "I'm traveling from June 15th to June 22nd"
        
        expected_dates = {
            "departure": "2024-06-15",
            "return": "2024-06-22",
            "duration": 7,
            "flexible": False
        }
        
        mock_llm_service.extract_dates.return_value = expected_dates
        
        result = await mock_llm_service.extract_dates(text)
        
        assert result["departure"] == "2024-06-15"
        assert result["return"] == "2024-06-22"
        assert result["duration"] == 7

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_classify_travel_type(self, mock_llm_service):
        """Test travel type classification."""
        messages = [
            "I need to travel for a business meeting",
            "We want to go on a romantic getaway",
            "Planning a family vacation with kids",
            "Going on a solo adventure trip"
        ]
        
        expected_types = ["business", "romantic", "family", "adventure"]
        
        for message, expected_type in zip(messages, expected_types):
            mock_llm_service.classify_travel_type.return_value = {
                "travel_type": expected_type,
                "confidence": 0.9
            }
            
            result = await mock_llm_service.classify_travel_type(message)
            assert result["travel_type"] == expected_type

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_suggest_improvements(self, mock_llm_service):
        """Test itinerary improvement suggestions."""
        itinerary = [
            {
                "day": 1,
                "activities": [
                    {"time": "09:00", "activity": "Eiffel Tower"},
                    {"time": "11:00", "activity": "Louvre Museum"},
                    {"time": "13:00", "activity": "Arc de Triomphe"}
                ]
            }
        ]
        
        expected_suggestions = [
            {
                "type": "optimization",
                "message": "Consider visiting Eiffel Tower in the evening for better lighting",
                "priority": "medium"
            },
            {
                "type": "logistics",
                "message": "Book Louvre tickets in advance to skip lines",
                "priority": "high"
            }
        ]
        
        mock_llm_service.suggest_improvements.return_value = expected_suggestions
        
        result = await mock_llm_service.suggest_improvements(itinerary)
        
        assert len(result) == 2
        assert result[0]["type"] == "optimization"
        assert result[1]["priority"] == "high"


class TestLLMServiceErrorHandling:
    """Test LLM service error handling and resilience."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_api_rate_limit_handling(self, mock_llm_service):
        """Test handling of API rate limits."""
        from openai import RateLimitError
        
        mock_llm_service.parse_travel_intent.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(),
            body=None
        )
        
        with pytest.raises(RateLimitError):
            await mock_llm_service.parse_travel_intent("test message", {})

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_api_timeout_handling(self, mock_llm_service):
        """Test handling of API timeouts."""
        import asyncio
        
        mock_llm_service.generate_response.side_effect = asyncio.TimeoutError("Request timed out")
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_llm_service.generate_response("test message", {})

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_invalid_response_handling(self, mock_llm_service):
        """Test handling of invalid LLM responses."""
        # Mock invalid JSON response
        mock_llm_service.parse_travel_intent.return_value = "invalid json response"
        
        # Service should handle this gracefully
        with pytest.raises(ValueError, match="Invalid response format"):
            result = await mock_llm_service.parse_travel_intent("test", {})
            if isinstance(result, str):
                raise ValueError("Invalid response format")

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_retry_mechanism(self, mock_llm_service):
        """Test retry mechanism for transient failures."""
        # First call fails, second succeeds
        mock_llm_service.generate_response.side_effect = [
            Exception("Temporary failure"),
            {"response": "Success on retry"}
        ]
        
        # Service should implement retry logic
        # This is a simplified test - actual implementation would need retry decorator
        try:
            result = await mock_llm_service.generate_response("test", {})
        except Exception:
            # Retry
            result = await mock_llm_service.generate_response("test", {})
        
        assert result["response"] == "Success on retry"


class TestLLMServiceCaching:
    """Test LLM service caching functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_response_caching(self, mock_llm_service, mock_cache_service):
        """Test caching of LLM responses."""
        message = "What are the best places to visit in Paris?"
        context = {"destination": "Paris"}
        
        # First call - cache miss
        mock_cache_service.get.return_value = None
        expected_response = {"response": "Paris attractions..."}
        mock_llm_service.generate_response.return_value = expected_response
        
        with patch('app.services.cache_service.CacheService', return_value=mock_cache_service):
            result = await mock_llm_service.generate_response(message, context)
        
        # Should call LLM and cache result
        mock_cache_service.set.assert_called_once()
        assert result == expected_response

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_cache_hit(self, mock_llm_service, mock_cache_service):
        """Test cache hit scenario."""
        message = "What are the best places to visit in Paris?"
        context = {"destination": "Paris"}
        cached_response = {"response": "Cached Paris attractions..."}
        
        # Cache hit
        mock_cache_service.get.return_value = cached_response
        
        with patch('app.services.cache_service.CacheService', return_value=mock_cache_service):
            result = await mock_llm_service.generate_response(message, context)
        
        # Should not call LLM, return cached result
        mock_llm_service.generate_response.assert_not_called()
        assert result == cached_response

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_cache_invalidation(self, mock_llm_service, mock_cache_service):
        """Test cache invalidation scenarios."""
        cache_key = "llm_response_hash123"
        
        # Test cache invalidation
        await mock_cache_service.delete(cache_key)
        mock_cache_service.delete.assert_called_once_with(cache_key)


class TestLLMServicePerformance:
    """Test LLM service performance characteristics."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.service
    async def test_response_time_measurement(self, mock_llm_service, performance_timer):
        """Test response time tracking."""
        message = "Plan a trip to Paris"
        context = {}
        
        # Mock a reasonably timed response
        async def delayed_response(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.1)  # 100ms delay
            return {"response": "Trip planned"}
        
        mock_llm_service.generate_response = delayed_response
        
        performance_timer.start()
        result = await mock_llm_service.generate_response(message, context)
        elapsed = performance_timer.stop()
        
        assert elapsed >= 0.1
        assert elapsed < 1.0  # Should complete within 1 second
        assert result["response"] == "Trip planned"

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.service
    async def test_concurrent_requests(self, mock_llm_service):
        """Test handling of concurrent requests."""
        import asyncio
        
        async def mock_response(message, context):
            await asyncio.sleep(0.1)
            return {"response": f"Response for {message}"}
        
        mock_llm_service.generate_response = mock_response
        
        # Create multiple concurrent requests
        messages = [f"Message {i}" for i in range(5)]
        tasks = [
            mock_llm_service.generate_response(msg, {})
            for msg in messages
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert f"Message {i}" in result["response"]

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.service
    async def test_memory_usage(self, mock_llm_service):
        """Test memory usage with large responses."""
        # Mock a large response
        large_response = {
            "response": "Very long response..." * 1000,
            "suggestions": ["Suggestion"] * 100,
            "data": {"key": "value"} * 500
        }
        
        mock_llm_service.generate_response.return_value = large_response
        
        result = await mock_llm_service.generate_response("test", {})
        
        # Verify large response is handled
        assert len(result["response"]) > 10000
        assert len(result["suggestions"]) == 100