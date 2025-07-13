# Pathavana Backend API

The backend API for Pathavana's AI-powered travel planning platform. Built with FastAPI, SQLAlchemy, and modern async Python patterns.

## 🏗️ Architecture

This backend implements a **unified conversational travel planning architecture** with:

- **Unified Travel Sessions**: Single conversation thread handling all travel needs
- **AI-Powered Orchestration**: LLM-driven intent detection and action planning
- **Flexible External Integration**: Modular service layer for travel APIs
- **Real-time Context Management**: Stateful conversation with persistent context
- **Scalable Caching**: Multi-layer caching for performance optimization

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── core/                       # Core configuration and database
│   │   ├── config.py              # Environment and settings
│   │   ├── database.py            # Database connection and session management
│   │   └── security.py            # Authentication and authorization
│   ├── api/                        # API endpoint definitions
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
├── cache/                         # File-based cache storage
├── .env.example                   # Environment variables template
├── full_backend_test.py           # Backend testing script
└── start-backend.sh               # Startup script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for caching)

### 1. Setup Environment

```bash
# Clone and navigate to backend directory
cd pathavana/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb pathavana

# Run database migrations
alembic upgrade head
```

### 4. Start the Server

```bash
# Using the startup script (recommended)
./start-backend.sh

# Or manually with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the API

```bash
# Run comprehensive backend tests
python full_backend_test.py

# Or test individual endpoints
curl http://localhost:8000/health
```

## 🔑 Key Features

### Unified Travel API

```bash
# Start a conversation
POST /api/v1/travel/chat
{
  "message": "I want to plan a trip to Paris",
  "session_id": null
}

# Continue the conversation
POST /api/v1/travel/chat  
{
  "message": "Find me flights from New York on December 15th",
  "session_id": "session-uuid-here"
}
```

### AI-Powered Features

- **Intent Detection**: Automatically understands user requests
- **Context Management**: Remembers conversation context across messages
- **Smart Recommendations**: AI-driven suggestions based on preferences
- **Natural Language Processing**: Handles complex, multi-part requests

### External Integrations

- **Amadeus API**: Flight and hotel search
- **LLM Integration**: OpenAI GPT-4 and Anthropic Claude support
- **Caching Layer**: Redis and file-based caching for performance

## 📊 API Documentation

Once the server is running, visit:

- **Interactive API Docs**: http://localhost:8000/api/v1/docs
- **ReDoc Documentation**: http://localhost:8000/api/v1/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v1/openapi.json

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pathavana

# External APIs
AMADEUS_API_KEY=your_amadeus_key
OPENAI_API_KEY=your_openai_key

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Security
SECRET_KEY=your-secret-key
```

### Database Configuration

The app uses PostgreSQL with async SQLAlchemy. Key models:

- **UnifiedTravelSession**: Core conversation and context storage
- **User/TravelerProfile**: User management and preferences  
- **Booking**: Comprehensive booking management
- **ConversationMessage**: Chat history and AI metadata

## 🧪 Testing

### Automated Testing

```bash
# Run all backend tests
python full_backend_test.py

# Test specific functionality
pytest tests/test_travel_api.py -v
```

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Start conversation
curl -X POST http://localhost:8000/api/v1/travel/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Tokyo"}'
```

## 📈 Performance & Scaling

### Caching Strategy

- **LLM Response Caching**: 24-hour cache for AI responses
- **API Result Caching**: 1-2 hour cache for external API calls
- **Session State Caching**: In-memory session management

### Database Optimization

- **UUID-based sessions**: Scalable session management
- **JSONB storage**: Flexible schema evolution
- **Strategic indexing**: Optimized query performance

## 🔒 Security

### Authentication

- JWT-based authentication
- Session-based anonymous access
- API key management for external services

### Data Privacy

- GDPR compliance endpoints
- Data export and deletion capabilities
- Privacy settings management

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   sudo service postgresql status
   
   # Verify database exists
   psql -l | grep pathavana
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

3. **API Key Issues**
   ```bash
   # Verify environment variables
   python -c "from app.core.config import settings; print(settings.AMADEUS_API_KEY[:10])"
   ```

### Logs

- Application logs: `logs/app.log`
- Database logs: Check PostgreSQL logs
- Error tracking: Configure Sentry DSN in `.env`

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Run the test suite before submitting changes

## 📝 License

This project is part of the Pathavana travel planning platform.