# Pathavana Testing Guide

This guide covers the comprehensive testing infrastructure for the Pathavana travel planning application, including backend API tests, frontend component tests, integration tests, and end-to-end testing.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Running Tests](#running-tests)
- [Coverage Requirements](#coverage-requirements)
- [CI/CD Pipeline](#cicd-pipeline)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Pathavana testing infrastructure includes:

- **Backend Tests**: API endpoints, services, models, and database operations
- **Frontend Tests**: React components, hooks, utilities, and user interactions  
- **Integration Tests**: Full application workflows and API contracts
- **End-to-End Tests**: Complete user journeys using Playwright
- **Performance Tests**: Load testing and performance benchmarks
- **Security Tests**: Vulnerability scanning and security analysis

### Test Types

| Type | Description | Tools | Coverage |
|------|-------------|-------|----------|
| Unit | Individual functions/components | pytest, Jest | 80%+ |
| Integration | Service interactions | pytest, RTL | 70%+ |
| API | Endpoint testing | pytest, httpx | 90%+ |
| E2E | User workflows | Playwright | Key flows |
| Performance | Load/stress testing | Lighthouse, k6 | Critical paths |

## 🏗️ Test Structure

```
pathavana/
├── backend/
│   ├── tests/
│   │   ├── conftest.py              # Pytest configuration & fixtures
│   │   ├── test_api/                # API endpoint tests
│   │   │   ├── test_auth.py         # Authentication tests
│   │   │   ├── test_travel_unified.py # Travel API tests
│   │   │   ├── test_bookings.py     # Booking API tests
│   │   │   └── test_travelers.py    # Traveler API tests
│   │   ├── test_services/           # Service layer tests
│   │   │   ├── test_llm_service.py  # LLM service tests
│   │   │   ├── test_amadeus_service.py # Amadeus API tests
│   │   │   ├── test_trip_context_service.py # Context service
│   │   │   └── test_cache_service.py # Cache service tests
│   │   └── test_models/             # Database model tests
│   │       ├── test_unified_session.py # Session model tests
│   │       └── test_user.py         # User model tests
│   └── pytest.ini                  # Pytest configuration
├── frontend/
│   ├── src/
│   │   ├── tests/
│   │   │   ├── utils/               # Test utilities
│   │   │   │   ├── testUtils.tsx    # Custom render functions
│   │   │   │   ├── mockData.ts      # Mock data generators
│   │   │   │   └── mockServer.ts    # MSW server setup
│   │   │   ├── components/          # Component tests
│   │   │   ├── hooks/               # Hook tests
│   │   │   └── integration/         # Integration tests
│   │   └── setupTests.ts           # Jest setup configuration
├── .github/workflows/test.yml      # CI/CD pipeline
└── run-tests.sh                    # Local test runner
```

## 🐍 Backend Testing

### Configuration

Backend tests use pytest with async support and comprehensive fixtures:

```python
# pytest.ini
[tool:pytest]
testpaths = tests
asyncio_mode = auto
addopts = --cov=app --cov-report=html --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    api: API endpoint tests
    external: Tests requiring external services
```

### Key Features

- **Async Testing**: Full async/await support for database operations
- **Database Fixtures**: Automatic test database setup and cleanup
- **Mock Services**: Comprehensive mocking for external APIs (Amadeus, OpenAI, etc.)
- **JSONB Testing**: Specialized tests for PostgreSQL JSONB operations
- **Authentication**: Test fixtures for authenticated requests

### Example API Test

```python
@pytest.mark.asyncio
@pytest.mark.api
async def test_create_travel_session(async_client: AsyncClient, auth_headers):
    """Test creating a new travel session."""
    session_data = {
        "initial_message": "I want to plan a trip to Paris",
        "travel_intent": {
            "destination": "Paris",
            "travel_type": "leisure"
        }
    }
    
    response = await async_client.post(
        "/api/v1/travel/sessions",
        json=session_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "active"
```

### Running Backend Tests

```bash
# All backend tests
./run-tests.sh backend

# Specific test types
./run-tests.sh backend-unit     # Unit tests only
./run-tests.sh backend-api      # API tests only
./run-tests.sh backend-models   # Model tests only

# With options
./run-tests.sh backend --verbose --parallel
```

## ⚛️ Frontend Testing

### Configuration

Frontend tests use Jest and React Testing Library with custom utilities:

```typescript
// setupTests.ts
import '@testing-library/jest-dom';
import { server } from './tests/utils/mockServer';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Key Features

- **Custom Render**: Render components with all necessary providers
- **Mock Services**: MSW for API mocking
- **User Interactions**: Comprehensive user event testing
- **Accessibility**: Built-in a11y testing
- **Performance**: Render time measurement

### Example Component Test

```typescript
import { render, screen, userEvent } from '../utils/testUtils';
import { ChatInput } from '../../components/ChatInput';

describe('ChatInput', () => {
  it('sends message when form is submitted', async () => {
    const user = userEvent.setup();
    const mockOnSend = jest.fn();
    
    render(<ChatInput onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    const button = screen.getByRole('button', { name: /send/i });
    
    await user.type(input, 'Hello, I want to visit Paris');
    await user.click(button);
    
    expect(mockOnSend).toHaveBeenCalledWith('Hello, I want to visit Paris');
    expect(input).toHaveValue('');
  });
});
```

### Running Frontend Tests

```bash
# All frontend tests
./run-tests.sh frontend

# Watch mode for development
./run-tests.sh frontend --watch

# Unit tests only
./run-tests.sh frontend-unit

# With coverage
./run-tests.sh coverage
```

## 🔄 Integration & E2E Testing

### Integration Tests

Integration tests verify complete workflows:

```typescript
describe('Travel Booking Flow', () => {
  it('completes full booking process', async () => {
    const user = userEvent.setup();
    
    render(<UnifiedTravelRequest />, { authenticated: true });
    
    // Search for flights
    await user.type(screen.getByLabelText(/destination/i), 'Paris');
    await user.click(screen.getByRole('button', { name: /search/i }));
    
    // Select flight
    await waitFor(() => {
      expect(screen.getByText(/air france/i)).toBeInTheDocument();
    });
    
    await user.click(screen.getByRole('button', { name: /select flight/i }));
    
    // Verify booking summary
    expect(screen.getByText(/booking summary/i)).toBeInTheDocument();
  });
});
```

### End-to-End Tests

E2E tests use Playwright for full browser automation:

```typescript
// e2e/travel-booking.spec.ts
import { test, expect } from '@playwright/test';

test('user can search and book a trip', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Login
  await page.click('[data-testid="login-button"]');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('[type="submit"]');
  
  // Search for trip
  await page.fill('[data-testid="destination-input"]', 'Paris');
  await page.click('[data-testid="search-button"]');
  
  // Verify results
  await expect(page.locator('[data-testid="flight-results"]')).toBeVisible();
  
  // Select and book
  await page.click('[data-testid="select-flight"]:first-child');
  await expect(page.locator('[data-testid="booking-summary"]')).toBeVisible();
});
```

## 🚀 Running Tests

### Quick Commands

```bash
# Run all tests
./run-tests.sh all

# Setup test environment
./run-tests.sh setup

# Generate coverage reports
./run-tests.sh coverage

# Run E2E tests
./run-tests.sh e2e

# Clean test artifacts
./run-tests.sh clean
```

### Test Options

| Option | Description |
|--------|-------------|
| `--watch` | Run in watch mode |
| `--verbose` | Detailed output |
| `--parallel` | Parallel execution |
| `--fast` | Skip slow tests |

### Environment Variables

```bash
# Backend Testing
export DATABASE_URL="postgresql+asyncpg://localhost/pathavana_test"
export REDIS_URL="redis://localhost:6379/1"
export TESTING=1

# Frontend Testing  
export REACT_APP_API_BASE_URL="http://localhost:8000"
export REACT_APP_ENVIRONMENT="test"
```

## 📊 Coverage Requirements

### Minimum Coverage Thresholds

| Component | Lines | Functions | Branches | Statements |
|-----------|-------|-----------|----------|------------|
| Backend API | 90% | 90% | 85% | 90% |
| Backend Services | 85% | 85% | 80% | 85% |
| Backend Models | 80% | 80% | 75% | 80% |
| Frontend Components | 80% | 80% | 75% | 80% |
| Frontend Hooks | 85% | 85% | 80% | 85% |
| Frontend Utils | 90% | 90% | 85% | 90% |

### Coverage Reports

- **Backend**: `backend/htmlcov/index.html`
- **Frontend**: `frontend/coverage/lcov-report/index.html`
- **Combined**: Available in CI artifacts

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline includes:

1. **Backend Tests**: Unit, integration, API tests with PostgreSQL
2. **Frontend Tests**: Component, hook, integration tests
3. **E2E Tests**: Full browser automation with Playwright
4. **Security Tests**: Vulnerability scanning with Trivy and Semgrep
5. **Performance Tests**: Lighthouse CI for performance metrics
6. **Code Quality**: SonarCloud and CodeQL analysis

### Pipeline Stages

```yaml
jobs:
  backend-tests:     # Python/pytest tests
  frontend-tests:    # React/Jest tests  
  integration-tests: # Full stack tests
  security-tests:    # Security scanning
  performance-tests: # Performance testing
  code-quality:      # Quality analysis
```

### Branch Protection

- All tests must pass before merging
- Minimum 80% test coverage required
- Security scans must pass
- Code quality gates enforced

## ✏️ Writing Tests

### Test Guidelines

1. **Descriptive Names**: Test names should clearly describe what they test
2. **AAA Pattern**: Arrange, Act, Assert structure
3. **Single Responsibility**: One assertion per test when possible
4. **Mock External Dependencies**: Use mocks for external APIs
5. **Test Edge Cases**: Include error conditions and boundary cases

### Backend Test Example

```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_parse_travel_intent_with_dates(mock_llm_service):
    """Test travel intent parsing with specific dates."""
    # Arrange
    message = "I want to go to Tokyo from June 15-22"
    expected_intent = {
        "destination": "Tokyo",
        "travel_dates": {
            "departure": "2024-06-15",
            "return": "2024-06-22"
        }
    }
    mock_llm_service.parse_travel_intent.return_value = expected_intent
    
    # Act
    result = await mock_llm_service.parse_travel_intent(message, {})
    
    # Assert
    assert result["destination"] == "Tokyo"
    assert result["travel_dates"]["departure"] == "2024-06-15"
```

### Frontend Test Example

```typescript
describe('FlightCard', () => {
  it('displays flight information correctly', () => {
    // Arrange
    const mockFlight = createMockFlight({
      airline: 'Air France',
      price: { total: 850, currency: 'USD' }
    });
    
    // Act
    render(<FlightCard flight={mockFlight} />);
    
    // Assert
    expect(screen.getByText('Air France')).toBeInTheDocument();
    expect(screen.getByText('$850')).toBeInTheDocument();
  });
  
  it('calls onSelect when flight is selected', async () => {
    const user = userEvent.setup();
    const mockOnSelect = jest.fn();
    const mockFlight = createMockFlight();
    
    render(<FlightCard flight={mockFlight} onSelect={mockOnSelect} />);
    
    await user.click(screen.getByRole('button', { name: /select/i }));
    
    expect(mockOnSelect).toHaveBeenCalledWith(mockFlight);
  });
});
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Reset test database
./run-tests.sh setup
```

#### Frontend Test Timeouts
```bash
# Increase timeout in jest.config.js
testTimeout: 10000

# Or use async utilities
await waitFor(() => expect(element).toBeInTheDocument())
```

#### Mock Service Issues
```bash
# Clear Jest cache
npm test -- --clearCache

# Reset mocks in test
jest.clearAllMocks()
```

### Debug Commands

```bash
# Verbose test output
./run-tests.sh backend --verbose

# Run specific test file
pytest tests/test_api/test_auth.py::test_login_success -v

# Debug frontend test
npm test -- --no-coverage --verbose ChatInput.test.tsx
```

### Performance Issues

```bash
# Run tests in parallel
./run-tests.sh backend --parallel

# Skip slow tests
./run-tests.sh all --fast

# Profile test execution
pytest --durations=10
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [MSW (Mock Service Worker)](https://mswjs.io/)

## 🤝 Contributing

When contributing to tests:

1. Follow existing test patterns and conventions
2. Ensure all tests pass locally before submitting PR
3. Add tests for new features and bug fixes
4. Maintain or improve test coverage
5. Update this documentation for significant changes

---

For questions or issues with testing, please check the troubleshooting section or create an issue in the repository.