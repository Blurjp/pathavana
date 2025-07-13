# Pathavana - Comprehensive Implementation Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Database Design](#database-design)
6. [API Reference](#api-reference)
7. [Services and Business Logic](#services-and-business-logic)
8. [Setup and Installation](#setup-and-installation)
9. [Development Workflow](#development-workflow)
10. [Testing Strategy](#testing-strategy)
11. [Deployment](#deployment)
12. [Security and Compliance](#security-and-compliance)

---

## Project Overview

### What is Pathavana?
Pathavana is a modern, AI-powered travel planning application that helps users discover, plan, and book travel experiences through a conversational interface. It combines natural language processing with real-time travel data from multiple sources to provide personalized travel recommendations and booking capabilities.

### Key Features
- **Conversational Planning**: Natural language chat interface for travel planning
- **Multi-Source Search**: Integration with Amadeus, Skyscanner, Booking.com, and other APIs
- **AI-Powered Recommendations**: LLM-based destination suggestions and itinerary planning
- **Real-time Booking**: Direct booking capabilities for flights, hotels, and activities
- **Session Management**: Persistent travel sessions with UUID-based tracking
- **User Profiles**: Comprehensive traveler profiles with preferences and documents
- **GDPR Compliance**: Full data privacy and compliance features

### Technology Stack
**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- Axios for API communication
- Custom hooks for state management
- CSS Modules + Tailwind CSS for styling

**Backend:**
- Python 3.9+ with FastAPI
- SQLAlchemy 2.0 with async PostgreSQL
- LangChain for AI agent orchestration
- Azure OpenAI for natural language processing
- gRPC for high-performance communication

**Database:**
- PostgreSQL 14+ with JSONB support
- Alembic for database migrations
- Redis for caching (optional)

**External Services:**
- Amadeus API for flight/hotel data
- Azure OpenAI for LLM capabilities
- Google Maps API for geocoding
- OAuth providers (Google, Facebook, Microsoft)

---

## Architecture Overview

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React)       │    │   (FastAPI)     │    │   Services      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Pages         │◄──►│ • API Endpoints │◄──►│ • Amadeus API   │
│ • Components    │    │ • Services      │    │ • Azure OpenAI  │
│ • Hooks         │    │ • AI Agents     │    │ • Google Maps   │
│ • State Mgmt    │    │ • Database      │    │ • OAuth         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Design Principles
1. **UUID-Based Session Management**: Single UUID flows through entire system
2. **Event-Driven Architecture**: Asynchronous processing with clear event boundaries
3. **Service-Oriented Design**: Clear separation of concerns between services
4. **AI-First Approach**: Natural language as primary user interface
5. **JSONB Flexibility**: Schema-less data storage for rapid feature development
6. **Progressive Enhancement**: Graceful degradation when services unavailable

### Key Architectural Patterns
- **Adapter Pattern**: For database migration and backward compatibility
- **Orchestrator Pattern**: AI agent coordination and conversation management
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Service instantiation and dependency injection
- **Circuit Breaker**: External service failure handling

---

## Backend Implementation

### Project Structure
```
backend/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── core/                       # Core configuration and database
│   │   ├── config.py              # Environment and settings
│   │   ├── database.py            # Database connection and session management
│   │   └── security.py            # Authentication and authorization
│   ├── api/                        # API endpoint definitions
│   │   ├── __init__.py
│   │   ├── travel_unified.py      # Main unified travel API
│   │   ├── bookings.py            # Booking management endpoints
│   │   ├── travelers.py           # Traveler profile endpoints
│   │   └── data_compliance.py     # GDPR compliance endpoints
│   ├── models/                     # Database models (SQLAlchemy)
│   │   ├── unified_travel_session.py  # Core session model
│   │   ├── user.py                # User and profile models
│   │   ├── booking.py             # Booking-related models
│   │   └── traveler.py            # Traveler profile models
│   ├── services/                   # Business logic services
│   │   ├── unified_travel_service.py  # Main travel orchestration
│   │   ├── llm_service.py         # AI/LLM integration
│   │   ├── amadeus_service.py     # External API integration
│   │   ├── destination_resolver.py    # Smart location resolution
│   │   ├── trip_context_service.py    # Conversation context
│   │   └── cache_service.py       # Caching and performance
│   ├── agents/                     # AI agent implementation
│   │   ├── unified_orchestrator.py    # Main conversation orchestrator
│   │   └── tools/                 # AI agent tools
│   │       ├── flight_tools.py    # Flight search and booking tools
│   │       ├── hotel_tools.py     # Hotel search tools
│   │       └── activity_tools.py  # Activity recommendation tools
│   └── schemas/                    # Pydantic request/response schemas
├── requirements.txt                # Python dependencies
├── alembic/                       # Database migrations
├── logs/                          # Application logs
└── cache/                         # File-based cache storage
```

### Core Application Entry Point
**`app/main.py`** - FastAPI application with:
- CORS middleware for frontend communication
- Trusted host middleware for security
- Lifespan management for startup/shutdown operations
- gRPC server initialization (port 50051)
- Health check and monitoring endpoints

### Database Models Architecture

#### Unified Travel Session Model
The system uses a **unified session approach** where all travel-related data is stored in a single model with JSONB columns for flexibility:

```python
class UnifiedTravelSession(Base):
    """Single source of truth for entire travel session"""
    session_id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(SessionStatus))
    
    # Flexible JSONB storage
    session_data = Column(JSONB)    # Chat, search results, UI state
    plan_data = Column(JSONB)       # Trip plans and itineraries
    session_metadata = Column(JSONB)  # Analytics and debugging info
    
    # Timestamps and relationships
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    last_activity_at = Column(DateTime)
```

#### Supporting Models
- **UnifiedSavedItem**: Items saved to travel sessions
- **UnifiedBooking**: Booking records with external provider tracking
- **User**: Complete user profiles with preferences
- **Traveler**: Individual traveler profiles for group bookings

### API Architecture

#### Unified Travel API (`/api/travel`)
Primary endpoint handling all travel operations:
- Session management and chat functionality
- Location and date updates
- Search orchestration (flights, hotels, activities)
- Saved items and trip planning
- Booking operations

#### Authentication Flow
- JWT-based authentication with Bearer tokens
- OAuth integration (Google, Facebook, Microsoft)
- Automatic token refresh and session management
- Role-based access control for admin functions

#### Request/Response Patterns
All API responses follow consistent structure:
```json
{
  "success": true,
  "data": { /* Response data */ },
  "metadata": {
    "session_id": "uuid",
    "timestamp": "ISO-8601",
    "version": "2.0"
  },
  "errors": []  // Only present if success: false
}
```

---

## Frontend Implementation

### Project Structure
```
frontend/
├── src/
│   ├── App.tsx                     # Root application component
│   ├── pages/                      # Page-level components
│   │   ├── TravelRequest.tsx       # Main chat interface
│   │   ├── UnifiedTravelRequest.tsx # UUID-based session version
│   │   ├── Trips.tsx              # User's saved trips
│   │   ├── Profile.tsx            # User profile management
│   │   └── Travelers.tsx          # Traveler profile management
│   ├── components/                 # Reusable UI components
│   │   ├── ChatInput.tsx          # Smart chat input with history
│   │   ├── SearchResultsSidebar.tsx # Flight/hotel results display
│   │   ├── FlightCard.tsx         # Individual flight option
│   │   ├── HotelCard.tsx          # Individual hotel option
│   │   ├── InteractiveMap.tsx     # Map visualization
│   │   └── Header.tsx             # Navigation and user menu
│   ├── hooks/                      # Custom React hooks
│   │   ├── useChatManager.ts      # Chat state and history
│   │   ├── useSessionManager.ts   # Session persistence
│   │   ├── useTripContext.ts      # Trip planning context
│   │   ├── useUnifiedSession.ts   # UUID-based session management
│   │   └── useAuth.ts             # Authentication state
│   ├── services/                   # API integration layer
│   │   ├── api.ts                 # Main API client
│   │   ├── unifiedTravelApi.ts    # Unified travel API
│   │   ├── travelApi.ts           # Legacy API endpoints
│   │   └── contextAPI.ts          # Context operations
│   ├── contexts/                   # React contexts
│   │   ├── AuthContext.tsx        # Authentication state
│   │   └── SidebarContext.tsx     # UI state management
│   ├── types/                      # TypeScript definitions
│   │   ├── TravelRequestTypes.ts  # Core travel types
│   │   ├── User.ts                # User-related types
│   │   └── index.ts               # Type exports
│   ├── utils/                      # Utility functions
│   │   ├── dateHelpers.ts         # Date parsing and formatting
│   │   ├── sessionStorage.ts      # Browser storage utilities
│   │   └── errorHandler.ts        # Error handling utilities
│   └── styles/                     # CSS and styling
├── public/                         # Static assets
├── package.json                    # Dependencies and scripts
└── jest.config.js                  # Testing configuration
```

### Key Frontend Components

#### Main Chat Interface (`TravelRequest.tsx`)
- Real-time chat with conversation history
- Smart input with arrow key navigation
- Session persistence and recovery
- Integration with search results sidebar
- Contextual prompt suggestions

#### Session Management (`useSessionManager.ts`)
```typescript
interface SessionData {
  sessionId: string;
  chatHistory: ChatMessage[];
  searchResults: SearchResults;
  tripContext: TripContext;
  lastUpdated: string;
}

const useSessionManager = () => {
  // Automatic session creation and recovery
  // Local storage synchronization
  // Server-side session persistence
  // URL-based session loading
};
```

#### Search Results Integration
- Live search results display
- Filter and sort capabilities
- Add-to-trip functionality
- Real-time price updates
- Comparison features

### State Management Patterns

#### Session-Based State
- Primary state stored in session objects
- Local storage for persistence
- Server synchronization on changes
- URL routing for session access

#### Context Providers
- **AuthContext**: User authentication and profile
- **SidebarContext**: UI state and sidebar visibility
- **TripContext**: Active trip planning state

#### Custom Hooks Pattern
All complex state logic encapsulated in custom hooks:
- `useChatManager`: Chat history and conversation flow
- `useSessionManager`: Session persistence and recovery
- `useTripContext`: Trip planning and saved items
- `useFlightSearch`: Flight search state management

---

## Database Design

### Schema Overview
The database uses a **hybrid approach** combining normalized tables for core entities with JSONB columns for flexible data storage.

#### Core Tables
```sql
-- Users and authentication
users                    # User accounts and basic info
user_profiles           # Extended profile information
travel_preferences      # User travel preferences
user_documents          # Passport, visa, etc.

-- Unified session model (current)
unified_travel_sessions # Main session table with JSONB
unified_saved_items     # Items saved to sessions
unified_bookings        # Booking records

-- Supporting tables
travelers               # Individual traveler profiles
bookings               # Detailed booking information
booking_travelers      # Traveler-booking relationships
flight_bookings        # Flight-specific details
hotel_bookings         # Hotel-specific details
activity_bookings      # Activity-specific details
```

#### JSONB Structure Examples

**Session Data JSONB:**
```json
{
  "chat_messages": [
    {
      "role": "user",
      "content": "I want to visit Paris next month",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant", 
      "content": "I'd love to help you plan your Paris trip!",
      "timestamp": "2024-01-15T10:30:05Z"
    }
  ],
  "parsed_intent": {
    "destination": "Paris",
    "departure_date": "2024-02-01",
    "return_date": "2024-02-08",
    "travelers": {"adults": 2, "children": 0},
    "budget": {"min": 1000, "max": 3000, "currency": "USD"}
  },
  "search_results": {
    "flights": [...],
    "hotels": [...],
    "activities": [...]
  },
  "ui_state": {
    "current_step": "selecting_flights",
    "expanded_panels": ["flights"],
    "filters": {...}
  }
}
```

**Plan Data JSONB:**
```json
{
  "title": "Paris Adventure",
  "destination_city": "Paris",
  "departure_city": "New York", 
  "departure_date": "2024-02-01",
  "return_date": "2024-02-08",
  "travelers_count": 2,
  "total_budget": {"amount": 2500, "currency": "USD"},
  "itinerary": {
    "day_1": {
      "date": "2024-02-01",
      "items": [
        {
          "type": "flight",
          "time": "08:00",
          "title": "Departure from JFK",
          "details": {...}
        }
      ]
    }
  }
}
```

### Migration Strategy
The system is transitioning from multiple tables to the unified model:
- **Current**: Unified model with JSONB storage
- **Legacy**: Normalized tables (backed up in `legacy_backup` schema)
- **Adapter**: `UnifiedToV2Adapter` provides backward compatibility

### Indexing Strategy
```sql
-- Performance indexes
CREATE INDEX idx_user_sessions ON unified_travel_sessions(user_id, created_at);
CREATE INDEX idx_session_status ON unified_travel_sessions(status);
CREATE INDEX idx_last_activity ON unified_travel_sessions(last_activity_at);

-- JSONB indexes for common queries
CREATE INDEX idx_session_destination 
ON unified_travel_sessions USING GIN ((session_data->'parsed_intent'->'destination'));
```

---

## API Reference

### Authentication Endpoints

#### POST `/api/auth/login`
Standard email/password authentication.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 123,
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

#### POST `/api/auth/google`
Google OAuth authentication.

### Unified Travel API

#### POST `/api/travel/sessions`
Create new travel session.

**Request:**
```json
{
  "message": "I want to visit Tokyo next spring",
  "source": "web"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "parsed_intent": {
      "destination": "Tokyo",
      "timeframe": "spring_2024",
      "confidence": 0.85
    },
    "suggestions": [
      "What time of year in spring works best for you?",
      "How many travelers will be joining you?"
    ]
  }
}
```

#### POST `/api/travel/sessions/{session_id}/chat`
Send message to existing session.

**Request:**
```json
{
  "message": "I'd like to travel in April for 2 people",
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "chat_input"
  }
}
```

#### GET `/api/travel/sessions/{session_id}`
Retrieve complete session data.

#### POST `/api/travel/sessions/{session_id}/search`
Trigger searches based on current session intent.

**Request:**
```json
{
  "search_types": ["flights", "hotels", "activities"],
  "force_refresh": false
}
```

#### POST `/api/travel/sessions/{session_id}/items`
Save item to trip plan.

**Request:**
```json
{
  "item_type": "flight",
  "item_data": {
    "flight_number": "UA123",
    "departure_time": "2024-04-01T08:00:00Z",
    "price": {"amount": 450, "currency": "USD"}
  },
  "assigned_day": 1,
  "notes": "Morning departure preferred"
}
```

### Booking API

#### POST `/api/bookings`
Create new booking.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "booking_type": "flight",
  "provider": "amadeus",
  "booking_data": {
    "flight_offer": {...},
    "travelers": [
      {
        "id": "traveler_1",
        "name": {"first": "John", "last": "Doe"},
        "passport": "US123456789"
      }
    ]
  },
  "payment_method": "credit_card"
}
```

### Error Handling
All endpoints return consistent error responses:

```json
{
  "success": false,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Invalid date format",
      "field": "departure_date"
    }
  ],
  "metadata": {
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Rate Limiting
- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour
- **Search endpoints**: 60 requests/minute
- **Booking endpoints**: 10 requests/minute

---

## Services and Business Logic

### Core Service Architecture

#### Unified Travel Service
Central orchestrator for all travel operations:

```python
class UnifiedTravelService:
    """Main business logic coordinator"""
    
    async def process_message(self, session_id: str, message: str) -> Response:
        # 1. Load or create session
        # 2. Parse message intent using LLM
        # 3. Update session context
        # 4. Trigger appropriate searches
        # 5. Generate response with suggestions
        
    async def execute_search(self, session_id: str, search_types: List[str]):
        # Coordinate parallel searches across multiple APIs
        
    async def save_item_to_trip(self, session_id: str, item_data: Dict):
        # Add item to user's trip plan with conflict detection
```

#### LLM Service Integration
Handles all AI/natural language processing:

```python
class LLMService:
    """Azure OpenAI integration for natural language understanding"""
    
    async def parse_travel_query_to_json(self, query: str, context: Dict) -> Dict:
        # Convert natural language to structured travel data
        
    async def generate_suggestions(self, session_data: Dict) -> List[str]:
        # Generate contextual follow-up questions
        
    async def resolve_conflicts(self, conflicts: List[Dict]) -> Dict:
        # Intelligent conflict resolution using conversation context
```

#### Destination Resolver
5-layer fallback strategy for location resolution:

```python
class DestinationResolver:
    """Smart destination and city resolution"""
    
    async def resolve_destination(self, query: str) -> Dict:
        # Layer 1: Direct IATA/city code match
        # Layer 2: Fuzzy string matching
        # Layer 3: Regional mapping (e.g., "French Riviera" → cities)
        # Layer 4: Geocoding via external APIs
        # Layer 5: LLM-based interpretation
```

### External API Integration

#### Amadeus Service
Primary travel data provider:

```python
class AmadeusService:
    """Amadeus API integration for flights and hotels"""
    
    async def search_flights(self, origin: str, destination: str, dates: Dict):
        # Real-time flight search with caching
        
    async def search_hotels(self, city: str, checkin: str, checkout: str):
        # Hotel availability and pricing
        
    async def get_activities(self, city: str) -> List[Dict]:
        # Local attractions and experiences
```

#### Cache Service
Multi-level caching for performance:

```python
CACHE_TTL_SETTINGS = {
    'ai_recommendations': 24 * 3600,    # 24 hours
    'amadeus_activities': 6 * 3600,     # 6 hours  
    'amadeus_locations': 12 * 3600,     # 12 hours
    'chat_responses': 2 * 3600,         # 2 hours
    'ai_hints': 1 * 3600,               # 1 hour
}

class CacheService:
    """File-based caching with automatic expiration"""
    
    async def get_cached_response(self, key: str, ttl: int = None):
        # Retrieve cached data with TTL checking
        
    async def cache_response(self, key: str, data: Dict, ttl: int = None):
        # Store data with automatic expiration
```

### AI Agent Architecture

#### Orchestrator Pattern
LangGraph-based conversation management:

```python
class UnifiedOrchestrator:
    """AI conversation orchestrator using LangGraph"""
    
    def __init__(self):
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent() 
        self.activity_agent = ActivityAgent()
        
    async def process_message(self, session_id: str, message: str):
        # Route message to appropriate agent(s)
        # Coordinate multi-agent responses
        # Maintain conversation context
```

#### Agent Tools
Specialized tools for each travel domain:

```python
# Flight Tools
async def search_flights_tool(origin: str, destination: str, dates: Dict):
    """LangChain tool for flight search"""
    
async def book_flight_tool(flight_offer: Dict, travelers: List[Dict]):
    """LangChain tool for flight booking"""

# Hotel Tools  
async def search_hotels_tool(city: str, dates: Dict, preferences: Dict):
    """LangChain tool for hotel search"""

# Activity Tools
async def get_attractions_tool(city: str, interests: List[str]):
    """LangChain tool for activity recommendations"""
```

### Business Rules and Validation

#### Travel Context Management
Smart conflict resolution and data validation:

```python
@dataclass
class TripContext:
    """Comprehensive trip context with conflict tracking"""
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travelers: int = 1
    
    # Multi-city support
    destinations: Optional[List[str]] = None
    city_durations: Optional[Dict[str, int]] = None
    
    # Conflict resolution
    conflicts_resolved: List[str] = None
    confidence: float = 0.8
    
    def detect_conflicts(self, new_data: Dict) -> List[str]:
        """Identify data conflicts with existing context"""
        
    def resolve_conflicts(self, resolution_strategy: str) -> None:
        """Apply conflict resolution strategy"""
```

#### Data Validation Rules
- Departure date must be before return date
- Future dates only (with grace period for same-day bookings)
- Valid city/airport codes
- Traveler count limits (1-9 for most bookings)
- Budget validation with currency conversion
- Age restrictions for certain bookings

---

## Setup and Installation

### Prerequisites
- **Node.js 18+** for frontend development
- **Python 3.9+** for backend development
- **PostgreSQL 14+** with JSONB support
- **Redis** (optional, for enhanced caching)
- **Git** for version control

### Environment Setup

#### Backend Setup
```bash
# Clone repository
git clone <repository-url>
cd pathavana/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your API keys and database config

# Database setup
alembic upgrade head

# Verify installation
python full_backend_test.py
```

#### Frontend Setup
```bash
cd pathavana/frontend

# Install dependencies
npm install

# Environment configuration
cp .env.example .env.local
# Edit .env.local with your API endpoints

# Start development server
npm start

# Verify installation
npm test
```

### Required Environment Variables

#### Backend (`.env`)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pathavana
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/pathavana

# API Keys
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Authentication
SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret

# Optional
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### Frontend (`.env.local`)
```bash
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your_google_oauth_client_id
REACT_APP_ENVIRONMENT=development
```

### Database Setup

#### Create Database
```sql
-- PostgreSQL setup
CREATE DATABASE pathavana;
CREATE USER travel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pathavana TO travel_user;

-- Enable required extensions
\c pathavana;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
```

#### Run Migrations
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### External Service Setup

#### Amadeus API
1. Register at [Amadeus for Developers](https://developers.amadeus.com/)
2. Create application and obtain API keys
3. Add keys to backend `.env` file

#### Azure OpenAI
1. Create Azure OpenAI resource
2. Deploy GPT-4 or GPT-3.5-turbo model
3. Add endpoint and API key to backend `.env`

#### Google OAuth
1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add client ID to both backend and frontend `.env` files

---

## Development Workflow

### Starting the Application

#### Backend
```bash
cd backend
source venv/bin/activate

# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Use the provided script
./start-backedn.sh
```

#### Frontend
```bash
cd frontend
npm start
```

#### Full Stack Development
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm start

# Terminal 3: Database (if needed)
psql -d pathavana
```

### Code Quality Commands

#### Backend
```bash
# Code formatting
black app/
isort app/

# Linting
flake8 app/
mypy app/

# Testing
pytest
pytest -v  # Verbose output
pytest --cov=app  # With coverage
```

#### Frontend
```bash
# Linting and formatting
npm run lint
npm run format

# Testing
npm test
npm test -- --coverage
npm test -- --watchAll=false  # Single run
```

### Database Operations

#### Creating Migrations
```bash
cd backend
source venv/bin/activate

# Auto-generate migration
alembic revision --autogenerate -m "Description of changes"

# Manual migration
alembic revision -m "Manual migration description"
```

#### Migration Management
```bash
# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history

# Show current migration
alembic current
```

### Development Best Practices

#### Git Workflow
```bash
# Feature development
git checkout -b feature/new-feature
# Make changes...
git add .
git commit -m "feat(scope): description"
git push origin feature/new-feature
# Create pull request

# Bug fixes
git checkout -b fix/bug-description
# Make changes...
git commit -m "fix(scope): description"
```

#### Testing Workflow
1. **Write failing test first** (TDD approach)
2. **Implement minimal code** to make test pass
3. **Refactor** while keeping tests green
4. **Run full test suite** before committing

#### Code Review Checklist
- [ ] Tests written and passing
- [ ] Code follows style guidelines
- [ ] No hardcoded values or secrets
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Performance considerations addressed

---

## Testing Strategy

### Testing Philosophy
The application follows **Test-Driven Development (TDD)** principles with comprehensive test coverage across all layers.

### Backend Testing

#### Test Structure
```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_api/                # API endpoint tests
│   ├── test_auth.py
│   ├── test_travel_unified.py
│   └── test_bookings.py
├── test_services/           # Service layer tests
│   ├── test_llm_service.py
│   ├── test_amadeus_service.py
│   └── test_trip_context_service.py
├── test_models/             # Database model tests
│   ├── test_unified_session.py
│   └── test_user.py
└── test_agents/             # AI agent tests
    ├── test_orchestrator.py
    └── test_flight_tools.py
```

#### Testing Patterns
```python
# Example API test
@pytest.mark.asyncio
async def test_create_travel_session(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/travel/sessions",
        json={"message": "I want to visit Paris"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data["data"]

# Example service test with mocking
@pytest.mark.asyncio
async def test_llm_service_parse_query(mock_openai):
    service = LLMService()
    result = await service.parse_travel_query_to_json(
        "I want to go to Tokyo next spring for 2 people"
    )
    assert result["destination"] == "Tokyo"
    assert result["travelers"]["adults"] == 2
    assert "spring" in result["timeframe"]
```

#### Test Fixtures
```python
# conftest.py
@pytest.fixture
async def db_session():
    # Create test database session
    
@pytest.fixture
async def auth_headers(db_session):
    # Create test user and return auth headers
    
@pytest.fixture
def mock_amadeus():
    # Mock Amadeus API responses
```

### Frontend Testing

#### Test Structure
```
frontend/src/
├── __tests__/               # Component tests
│   ├── components/
│   │   ├── ChatInput.test.tsx
│   │   ├── SearchResultsSidebar.test.tsx
│   │   └── FlightCard.test.tsx
│   ├── hooks/
│   │   ├── useChatManager.test.tsx
│   │   └── useSessionManager.test.tsx
│   └── pages/
│       ├── TravelRequest.test.tsx
│       └── Profile.test.tsx
├── tests/                   # Integration tests
│   ├── TravelRequest.integration.test.tsx
│   └── BookingFlow.integration.test.tsx
└── setupTests.ts            # Test configuration
```

#### Testing Patterns
```typescript
// Component test example
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../components/ChatInput';

describe('ChatInput', () => {
  it('should handle message submission', () => {
    const onSubmit = jest.fn();
    render(<ChatInput onSubmit={onSubmit} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByText('Send'));
    
    expect(onSubmit).toHaveBeenCalledWith('Test message');
  });
});

// Hook test example
import { renderHook, act } from '@testing-library/react-hooks';
import { useChatManager } from '../hooks/useChatManager';

describe('useChatManager', () => {
  it('should add messages to history', () => {
    const { result } = renderHook(() => useChatManager());
    
    act(() => {
      result.current.addMessage('user', 'Hello');
    });
    
    expect(result.current.chatHistory).toHaveLength(1);
    expect(result.current.chatHistory[0].content).toBe('Hello');
  });
});
```

#### Mock Setup
```typescript
// setupTests.ts
import '@testing-library/jest-dom';

// Mock API calls
jest.mock('./services/api', () => ({
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;
```

### Integration Testing

#### End-to-End User Flows
```typescript
// Travel booking flow integration test
describe('Travel Booking Flow', () => {
  it('should complete full booking process', async () => {
    // 1. User login
    // 2. Start travel session
    // 3. Search for flights
    // 4. Select flight option
    // 5. Add to trip plan
    // 6. Complete booking
    // 7. Verify booking confirmation
  });
});
```

### Test Coverage Requirements
- **Minimum 80% code coverage** across all modules
- **100% coverage** for critical paths (authentication, booking, payment)
- **API endpoint tests** for all public endpoints
- **Component tests** for all UI interactions
- **Integration tests** for key user journeys

### Testing Commands
```bash
# Backend
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=app         # With coverage report
pytest -k "test_auth"    # Run specific tests

# Frontend
cd frontend
npm test                  # Interactive test runner
npm test -- --coverage   # With coverage report
npm test -- --watchAll=false  # Single run
```

---

## Deployment

### Production Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Servers   │    │   Database      │
│   (nginx)       │───►│   (Docker)      │───►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Cache/Redis   │
                       └─────────────────┘
```

### Docker Configuration

#### Backend Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_BASE_URL=http://backend:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/pathavana
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/cache:/app/cache

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=pathavana
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Environment-Specific Configurations

#### Production Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/pathavana
DATABASE_MAX_CONNECTIONS=20

# External APIs
AMADEUS_CLIENT_ID=prod_amadeus_client_id
AZURE_OPENAI_ENDPOINT=https://prod-endpoint.openai.azure.com/

# Security
SECRET_KEY=super-secure-production-key
JWT_ALGORITHM=HS256
ALLOWED_HOSTS=api.pathavana.com,www.pathavana.com

# Performance
REDIS_URL=redis://prod-redis:6379
CACHE_TTL_DEFAULT=3600

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

#### Staging Environment
```bash
# Similar to production but with staging APIs and relaxed security
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
AMADEUS_CLIENT_ID=staging_amadeus_client_id
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        # Docker build and deploy commands
        docker-compose -f docker-compose.prod.yml up -d
```

### Database Migration in Production

#### Zero-Downtime Migration Strategy
```bash
# 1. Create migration
alembic revision --autogenerate -m "Add new feature"

# 2. Test migration on staging
alembic upgrade head

# 3. Production deployment
# - Deploy new code with migration
# - Run migration during low-traffic window
# - Monitor for issues
# - Rollback plan ready
```

#### Backup Strategy
```bash
# Automated daily backups
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U user pathavana > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://pathavana-backups/
```

### Monitoring and Logging

#### Application Monitoring
- **Health checks** on `/health` endpoint
- **Metrics collection** via Prometheus
- **Error tracking** via Sentry
- **Performance monitoring** via New Relic/DataDog

#### Log Aggregation
```python
# Structured logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}
```

---

## Security and Compliance

### Authentication and Authorization

#### JWT Token Security
```python
# Token configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token validation
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user(user_id)
    if user is None:
        raise credentials_exception
    return user
```

#### OAuth Security
- **Secure redirect URIs** configured for production domains
- **State parameter** validation to prevent CSRF
- **PKCE (Proof Key for Code Exchange)** for mobile apps
- **Scope limitation** to minimum required permissions

### Data Security

#### Database Security
```sql
-- Row-level security for user data
ALTER TABLE unified_travel_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_sessions_policy ON unified_travel_sessions
    FOR ALL TO application_user
    USING (user_id = current_setting('app.current_user_id')::integer);

-- Encrypt sensitive fields
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Store encrypted payment data
UPDATE user_payment_methods 
SET account_number = pgp_sym_encrypt(account_number, 'encryption_key');
```

#### API Security
- **Rate limiting** implemented per endpoint and user
- **Input validation** using Pydantic schemas
- **SQL injection prevention** via parameterized queries
- **XSS protection** with proper output encoding
- **CORS configuration** restricted to known domains

### GDPR Compliance

#### Data Processing Principles
1. **Lawfulness, fairness, transparency**
2. **Purpose limitation** - data used only for travel planning
3. **Data minimization** - collect only necessary information
4. **Accuracy** - maintain up-to-date user data
5. **Storage limitation** - automatic data retention policies
6. **Integrity and confidentiality** - encryption and access controls
7. **Accountability** - audit trails and compliance documentation

#### Data Subject Rights Implementation
```python
class DataComplianceService:
    """GDPR compliance service"""
    
    async def export_user_data(self, user_id: int) -> Dict:
        """Right to data portability"""
        # Export all user data in structured format
        
    async def delete_user_data(self, user_id: int) -> bool:
        """Right to erasure ('right to be forgotten')"""
        # Permanently delete user data with audit trail
        
    async def anonymize_user_data(self, user_id: int) -> bool:
        """Anonymize user data for analytics"""
        # Remove personally identifiable information
        
    async def get_data_processing_log(self, user_id: int) -> List[Dict]:
        """Right to information about processing"""
        # Return audit log of data processing activities
```

#### Consent Management
```typescript
// Frontend consent management
interface ConsentData {
  necessary: boolean;      // Always true - required for service
  analytics: boolean;      // Optional - user choice
  marketing: boolean;      // Optional - user choice
  thirdParty: boolean;     // Optional - for external integrations
  timestamp: string;
  version: string;         // Consent version for tracking changes
}

const ConsentManager = {
  recordConsent: (consent: ConsentData) => {
    // Store consent with timestamp and version
  },
  
  checkConsent: (type: ConsentType) => {
    // Verify user has consented to specific processing
  },
  
  withdrawConsent: (type: ConsentType) => {
    // Allow user to withdraw consent
  }
};
```

### Security Best Practices

#### Environment Security
- **Environment variables** for all secrets and configuration
- **Secrets management** via AWS Secrets Manager or similar
- **Encryption at rest** for database and file storage
- **Encryption in transit** via HTTPS/TLS 1.3
- **Network security** with VPC and security groups

#### Application Security
```python
# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

#### Audit and Monitoring
```python
# Audit logging for sensitive operations
async def audit_log(user_id: int, action: str, resource: str, details: Dict):
    """Log all security-relevant activities"""
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,  # CREATE, READ, UPDATE, DELETE
        "resource": resource,  # travel_session, booking, user_data
        "details": details,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
    
    await store_audit_log(audit_entry)
```

### Incident Response Plan

#### Security Incident Categories
1. **Data Breach** - Unauthorized access to user data
2. **Service Disruption** - DDoS or system outages
3. **Account Compromise** - Unauthorized account access
4. **API Abuse** - Misuse of external API integrations

#### Response Procedures
1. **Detection** - Automated monitoring and alerting
2. **Assessment** - Determine scope and impact
3. **Containment** - Isolate affected systems
4. **Eradication** - Remove threat and vulnerabilities
5. **Recovery** - Restore normal operations
6. **Lessons Learned** - Post-incident review and improvements

---

## Conclusion

This comprehensive implementation guide provides a complete blueprint for building and maintaining the Pathavana application. The architecture emphasizes:

- **Modern Development Practices**: TDD, clean architecture, and comprehensive testing
- **Scalable Design**: Service-oriented architecture with clear separation of concerns
- **AI Integration**: LLM-powered natural language processing and intelligent agents
- **User Experience**: Conversational interface with persistent session management
- **Security and Compliance**: GDPR compliance and comprehensive security measures
- **Production Readiness**: Docker deployment, monitoring, and CI/CD pipelines

The system successfully combines cutting-edge AI capabilities with robust software engineering practices to deliver a sophisticated travel planning and booking platform.

### Key Success Factors
1. **UUID-based session management** provides consistency across all components
2. **JSONB storage strategy** enables rapid feature development and schema evolution
3. **AI agent architecture** delivers natural, conversational user interactions
4. **Comprehensive testing** ensures reliability and maintainability
5. **Security-first design** protects user data and ensures compliance
6. **Modular architecture** supports independent scaling and deployment

This implementation serves as a foundation for building similar AI-powered applications that require complex data relationships, real-time user interactions, and integration with multiple external services.