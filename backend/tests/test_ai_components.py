"""
Comprehensive tests for AI components in Pathavana.
Tests cover LLM service, orchestrator, and agent tools.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from app.services.llm_service import LLMService, AzureOpenAIService, OpenAIService, AnthropicService
from app.services.trip_context_service import TripContextService, TripContext, ConflictType, ResolutionStrategy
from app.agents.unified_orchestrator import UnifiedOrchestrator
from app.agents.tools.flight_tools import FlightTools
from app.agents.tools.hotel_tools import HotelTools
from app.agents.tools.activity_tools import ActivityTools


class TestLLMService:
    """Test cases for LLM service."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.services.llm_service.settings') as mock:
            mock.LLM_PROVIDER = "azure_openai"
            mock.AZURE_OPENAI_API_KEY = "test-key"
            mock.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com"
            mock.AZURE_OPENAI_API_VERSION = "2024-02-01"
            mock.AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
            mock.LLM_MODEL = "gpt-4"
            mock.LLM_TEMPERATURE = 0.7
            mock.LLM_MAX_TOKENS = 2000
            mock.ANTHROPIC_API_KEY = "test-anthropic-key"
            yield mock
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        with patch('app.services.llm_service.CacheService') as mock:
            cache_instance = AsyncMock()
            cache_instance.get_cached_response.return_value = None
            cache_instance.cache_response.return_value = None
            mock.return_value = cache_instance
            yield cache_instance
    
    @pytest.mark.asyncio
    async def test_llm_service_initialization(self, mock_settings, mock_cache_service):
        """Test LLM service initialization with different providers."""
        # Test Azure OpenAI initialization
        service = LLMService()
        assert service.provider == "azure_openai"
        assert service.primary_service is not None
        assert isinstance(service.primary_service, AzureOpenAIService)
    
    @pytest.mark.asyncio
    async def test_parse_travel_query_to_json(self, mock_settings, mock_cache_service):
        """Test parsing travel queries to JSON."""
        with patch.object(LLMService, '_generate_with_fallback') as mock_generate:
            mock_generate.return_value = json.dumps({
                "destinations": [{"name": "Paris", "type": "city"}],
                "dates": {
                    "departure": "2024-06-15",
                    "return": "2024-06-22",
                    "flexible": False
                },
                "travelers": {
                    "adults": 2,
                    "children": 0,
                    "infants": 0
                },
                "preferences": ["direct flights", "luxury hotels"]
            })
            
            service = LLMService()
            result = await service.parse_travel_query_to_json(
                "I want to go to Paris in June for a week with my partner"
            )
            
            assert result["destinations"][0]["name"] == "Paris"
            assert result["travelers"]["adults"] == 2
            assert "direct flights" in result["preferences"]
    
    @pytest.mark.asyncio
    async def test_generate_suggestions(self, mock_settings, mock_cache_service):
        """Test suggestion generation."""
        with patch.object(LLMService, '_generate_with_fallback') as mock_generate:
            mock_generate.return_value = json.dumps([
                "When would you like to travel to Paris?",
                "What's your budget for this trip?",
                "Are you interested in any specific activities?"
            ])
            
            service = LLMService()
            session_data = {
                "travel_context": {
                    "destinations": ["Paris"],
                    "travelers": {"adults": 2}
                }
            }
            
            suggestions = await service.generate_suggestions(session_data, max_suggestions=3)
            assert len(suggestions) == 3
            assert "Paris" in suggestions[0]
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts(self, mock_settings, mock_cache_service):
        """Test conflict resolution."""
        with patch.object(LLMService, '_generate_with_fallback') as mock_generate:
            mock_generate.return_value = json.dumps({
                "resolutions": {
                    "destination_city": "Paris",
                    "start_date": "2024-06-15"
                },
                "reasoning": "User explicitly mentioned June 15th in latest message",
                "confidence": 0.9
            })
            
            service = LLMService()
            conflicts = [
                {
                    "type": ConflictType.DESTINATION_CONFLICT,
                    "field": "destination_city",
                    "existing": "London",
                    "new": "Paris"
                }
            ]
            
            result = await service.resolve_conflicts(conflicts, {"destination_city": "London"})
            assert result["resolved"] == True
            assert result["resolution"]["resolutions"]["destination_city"] == "Paris"


class TestTripContextService:
    """Test cases for trip context service."""
    
    @pytest.fixture
    def context_service(self):
        """Create context service instance."""
        return TripContextService()
    
    def test_trip_context_dataclass(self):
        """Test TripContext dataclass functionality."""
        context = TripContext(
            departure_city="New York",
            destination_city="Paris",
            start_date="2024-06-15",
            end_date="2024-06-22",
            travelers={"adults": 2, "children": 0, "infants": 0}
        )
        
        assert context.departure_city == "New York"
        assert context.destination_city == "Paris"
        assert context.travelers["adults"] == 2
        assert context.confidence == 1.0
    
    def test_detect_conflicts(self):
        """Test conflict detection."""
        context = TripContext(
            destination_city="London",
            start_date="2024-06-10"
        )
        
        new_data = {
            "destination_city": "Paris",
            "start_date": "2024-06-15"
        }
        
        conflicts = context.detect_conflicts(new_data)
        assert len(conflicts) == 2
        assert conflicts[0]["type"] == ConflictType.DESTINATION_CONFLICT
        assert conflicts[1]["type"] == ConflictType.DATE_CONFLICT
    
    def test_resolve_conflicts_most_recent(self):
        """Test conflict resolution with most recent strategy."""
        context = TripContext(
            destination_city="London",
            start_date="2024-06-10"
        )
        
        conflicts = [
            {
                "type": ConflictType.DESTINATION_CONFLICT,
                "field": "destination_city",
                "existing": "London",
                "new": "Paris",
                "severity": "medium"
            }
        ]
        
        context.resolve_conflicts(conflicts, ResolutionStrategy.MOST_RECENT)
        assert context.destination_city == "Paris"
        assert len(context.conflicts_resolved) == 1
        assert context.confidence < 1.0
    
    def test_extract_destinations(self, context_service):
        """Test destination extraction from text."""
        message = "I want to fly from New York to Paris next month"
        destinations = context_service._extract_destinations(message)
        
        assert len(destinations) >= 1
        # Note: Actual resolution would depend on DestinationResolver
    
    def test_extract_dates(self, context_service):
        """Test date extraction from text."""
        message = "I want to travel on June 15th and return on June 22nd"
        dates = context_service._extract_dates(message)
        
        assert "departure" in dates or "return" in dates
    
    def test_extract_passengers(self, context_service):
        """Test passenger extraction from text."""
        message = "Trip for 2 adults and 1 child"
        passengers = context_service._extract_passengers(message)
        
        assert passengers.get("adults") == 2
        assert passengers.get("children") == 1
    
    def test_extract_preferences(self, context_service):
        """Test preference extraction from text."""
        message = "I want direct flights and luxury hotels with a pool"
        preferences = context_service._extract_preferences(message)
        
        assert "direct" in preferences
        assert "luxury" in preferences
        assert "pool" in preferences
    
    def test_validate_trip_context(self, context_service):
        """Test trip context validation."""
        context = {
            "destination_city": "Paris",
            "start_date": "2024-06-15",
            "travelers": {"adults": 2}
        }
        
        validation = context_service.validate_trip_context(context)
        assert validation["is_complete"] == True
        assert len(validation["missing_fields"]) == 0
        
        # Test incomplete context
        incomplete_context = {"destination_city": "Paris"}
        validation = context_service.validate_trip_context(incomplete_context)
        assert validation["is_complete"] == False
        assert "start_date" in validation["missing_fields"]


class TestUnifiedOrchestrator:
    """Test cases for unified orchestrator."""
    
    @pytest.fixture
    def mock_travel_service(self):
        """Mock travel service."""
        service = AsyncMock()
        service.create_session.return_value = "test-session-id"
        service.get_session_state.return_value = {
            "travel_context": {},
            "conversation_history": []
        }
        service.add_conversation_message.return_value = None
        service.update_session_context.return_value = None
        return service
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for orchestrator."""
        with patch('app.agents.unified_orchestrator.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.LLM_TEMPERATURE = 0.7
            mock_settings.LLM_MAX_TOKENS = 2000
            mock_settings.LLM_STREAMING_ENABLED = False
            yield
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mock_travel_service, mock_llm):
        """Test orchestrator initialization."""
        orchestrator = UnifiedOrchestrator(mock_travel_service)
        assert orchestrator.travel_service == mock_travel_service
        assert orchestrator.llm_service is not None
        assert len(orchestrator.tools) > 0
    
    @pytest.mark.asyncio
    async def test_search_flights_wrapper(self, mock_travel_service, mock_llm):
        """Test flight search tool wrapper."""
        orchestrator = UnifiedOrchestrator(mock_travel_service)
        
        with patch.object(orchestrator.flight_tools, 'search_flights') as mock_search:
            mock_search.return_value = {
                "flights": [
                    {
                        "airlines": ["United"],
                        "price": {"total": "500", "currency": "USD"},
                        "total_duration": "8h 30m",
                        "flight_type": "direct"
                    }
                ],
                "error": None
            }
            
            result = await orchestrator._search_flights_wrapper(
                origin="NYC",
                destination="LAX",
                departure_date="2024-06-15",
                adults=2
            )
            
            assert "Found 1 flight options" in result
            assert "United" in result
            assert "$500" in result


class TestAgentTools:
    """Test cases for agent tools."""
    
    @pytest.fixture
    def mock_amadeus_service(self):
        """Mock Amadeus service."""
        service = AsyncMock()
        service.search_flights.return_value = {
            "flights": [
                {
                    "id": "flight1",
                    "price": {"total": "500", "currency": "USD"},
                    "itineraries": [
                        {
                            "duration": "PT8H30M",
                            "segments": [
                                {
                                    "carrier": "UA",
                                    "departure": {"time": "2024-06-15T08:00:00"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        service.search_hotels.return_value = {
            "hotels": [
                {
                    "id": "hotel1",
                    "name": "Grand Hotel",
                    "rating": 4.5,
                    "price": {"total": "200"},
                    "amenities": ["wifi", "pool", "spa"]
                }
            ]
        }
        return service
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        service = AsyncMock()
        service.get_cached_flight_search.return_value = None
        service.cache_flight_search.return_value = None
        service.get_cached_hotel_search.return_value = None
        service.cache_hotel_search.return_value = None
        service.get.return_value = None
        service.set.return_value = None
        return service
    
    @pytest.mark.asyncio
    async def test_flight_tools_search(self, mock_amadeus_service, mock_cache_service):
        """Test flight search functionality."""
        flight_tools = FlightTools(mock_amadeus_service, mock_cache_service)
        
        search_params = {
            "origin": "NYC",
            "destination": "LAX",
            "departure_date": "2024-06-15",
            "adults": 2
        }
        
        result = await flight_tools.search_flights(search_params)
        assert len(result["flights"]) == 1
        assert result["flights"][0]["airlines"] == ["UA"]
        assert result["flights"][0]["convenience_score"] > 0
    
    @pytest.mark.asyncio
    async def test_hotel_tools_search(self, mock_amadeus_service, mock_cache_service):
        """Test hotel search functionality."""
        hotel_tools = HotelTools(mock_amadeus_service, mock_cache_service)
        
        search_params = {
            "city_code": "PAR",
            "check_in_date": "2024-06-15",
            "check_out_date": "2024-06-22",
            "adults": 2
        }
        
        result = await hotel_tools.search_hotels(search_params)
        assert len(result["hotels"]) == 1
        assert result["hotels"][0]["name"] == "Grand Hotel"
        assert result["hotels"][0]["value_score"] > 0
    
    @pytest.mark.asyncio
    async def test_activity_tools_recommendations(self, mock_cache_service):
        """Test activity recommendations."""
        activity_tools = ActivityTools(mock_cache_service)
        
        destination = {
            "resolved": {
                "city_name": "Paris",
                "country": "France"
            }
        }
        preferences = ["cultural", "food"]
        
        result = await activity_tools.get_activity_recommendations(
            destination,
            preferences,
            duration_days=3
        )
        
        assert "activities" in result
        assert "itinerary" in result
        assert result["preferences_applied"] == preferences


if __name__ == "__main__":
    pytest.main([__file__, "-v"])