# Claude Development Guidelines

## Project Overview
This is Pathavana, a travel planning application with a React/TypeScript frontend and Python/FastAPI backend. The system helps users plan trips by searching for flights, hotels, and activities through an AI-powered chat interface.

## Architecture Overview

### Frontend Architecture
```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page components (routes)
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API communication layer
│   ├── contexts/         # React contexts for global state
│   ├── utils/            # Utility functions
│   ├── types/            # TypeScript type definitions
│   └── styles/           # CSS files
```

### Backend Architecture
```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   ├── agents/           # AI orchestration
│   ├── core/             # Core configurations
│   └── schemas/          # Pydantic schemas
```

## Key Architecture Patterns

### Unified Session Management
Pathavana uses a **UUID-based unified session model** as the core architectural pattern:

- **Single Source of Truth**: `UnifiedTravelSession` model stores all travel data in JSONB columns
- **UUID Flow**: Single UUID flows through entire system (frontend → API → database)
- **JSONB Storage**: Flexible schema-less storage for rapid feature development
- **Session Persistence**: Sessions automatically saved to localStorage and server
- **Migration Strategy**: `UnifiedToV2Adapter` provides backward compatibility

### Core API Pattern
- **Unified Travel API** (`/api/travel`) handles all travel operations
- **Session-based operations** using consistent UUID parameter
- **Conversation context** maintained across all interactions
- **Real-time synchronization** between frontend and backend state

### AI Agent Architecture
- **Orchestrator Pattern**: `UnifiedOrchestrator` coordinates multiple AI agents
- **LangChain Integration**: Flight, Hotel, and Activity agents with specialized tools
- **Context Management**: `TripContextService` maintains conversation state
- **Conflict Resolution**: Intelligent handling of contradictory user inputs

## TDD (Test-Driven Development) Rules

### 1. Red-Green-Refactor Cycle
1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### 2. Test File Naming Convention
- Frontend: `ComponentName.test.tsx` or `fileName.test.ts`
- Backend: `test_module_name.py`

### 3. Test Structure
```typescript
// Frontend Example
describe('ComponentName', () => {
  beforeEach(() => {
    // Setup
  });

  it('should handle specific behavior', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = functionUnderTest(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

### UI Bug Fix Testing Rule
**CRITICAL**: Whenever you fix a UI-related bug, you MUST:
1. Create a test that reproduces the bug before the fix
2. Verify the test fails with the bug present
3. Apply the fix
4. Verify the test passes after the fix
5. Include edge cases and related scenarios

Example test structure for UI fixes:
```typescript
describe('UI Bug: Component requires double-click', () => {
  it('should work with single click after fix', () => {
    // Test the specific bug scenario
  });
  
  it('should handle edge cases', () => {
    // Test related scenarios
  });
});
```

```python
# Backend Example
import pytest

class TestServiceName:
    @pytest.fixture
    def setup(self):
        # Setup code
        pass
    
    async def test_specific_behavior(self, setup):
        # Arrange
        input_data = {"test": "data"}
        
        # Act
        result = await function_under_test(input_data)
        
        # Assert
        assert result == expected_value
```

### 4. Test Coverage Requirements
- Aim for 80% code coverage minimum
- Critical paths must have 100% coverage
- All API endpoints must have integration tests
- All UI interactions must have component tests

## Development Rules

### 1. Code Style
- **Frontend**: Follow ESLint and Prettier configurations
- **Backend**: Follow PEP 8 and use Black formatter
- Use meaningful variable and function names
- Keep functions small and focused (< 50 lines)

### 2. Git Commit Messages
```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(flight-search): add destination resolver for regions

- Implements 5-layer fallback strategy
- Handles regions like "Patagonia" and "French Riviera"
- Adds geocoding support for landmarks

Closes #123
```

### 3. Pull Request Guidelines
- PR title should follow commit message format
- Include description of changes
- Link related issues
- Ensure all tests pass
- Request review from at least one team member

### 4. API Design Principles
- RESTful conventions for endpoints
- Use proper HTTP status codes
- Version APIs (`/api/v1/`)
- Include request/response examples in documentation
- Use Pydantic schemas for validation

### 5. Database Guidelines
- Use migrations for all schema changes
- Never modify migrations after they're applied
- Include rollback procedures
- Test migrations on a copy of production data
- Use meaningful table and column names

### 6. Security Best Practices
- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Use parameterized queries
- Implement proper authentication/authorization
- Keep dependencies updated

### 7. Error Handling
```typescript
// Frontend
try {
  const result = await apiCall();
  // Handle success
} catch (error) {
  logger.error('Descriptive error message', error);
  // Show user-friendly error message
}
```

```python
# Backend
try:
    result = await service_call()
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    raise HTTPException(status_code=400, detail="User-friendly message")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 8. Performance Guidelines
- Implement caching for expensive operations
- Use pagination for large datasets
- Optimize database queries (avoid N+1)
- Lazy load components in frontend
- Monitor API response times

### 9. Documentation Requirements
- All public functions must have docstrings
- Complex algorithms need inline comments
- API endpoints must have OpenAPI documentation
- Maintain README files for each major module
- Keep architectural decision records (ADRs)

## Testing Strategy

### 1. Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Focus on edge cases
- Test error conditions

### 2. Integration Tests
- Test API endpoints end-to-end
- Test database operations
- Test external service integrations
- Use test database

### 3. Component Tests
- Test React components in isolation
- Test user interactions
- Test different states/props
- Use React Testing Library

### 4. E2E Tests (Optional)
- Test critical user journeys
- Run against staging environment
- Use tools like Cypress or Playwright

## Development Workflow

### 1. Feature Development
1. Create feature branch from `main`
2. Write failing tests
3. Implement feature
4. Ensure all tests pass
5. Update documentation
6. Create pull request
7. Address review feedback
8. Merge after approval

### 2. Bug Fixes
1. Write test to reproduce bug
2. Fix the bug
3. Ensure test passes
4. Verify no regressions
5. Create pull request with test

### 3. Refactoring
1. Ensure existing tests cover the code
2. Make incremental changes
3. Run tests after each change
4. Keep commits small and focused

### 4. Post-Fix Verification
**CRITICAL - ALWAYS RUN THE BACKEND SERVER TO VERIFY CHANGES**

**FIRST STEP - ACTIVATE VIRTUAL ENVIRONMENT**:
```bash
cd backend
source venv/bin/activate
```

After making any backend changes:
1. **MANDATORY**: Run `python full_backend_test.py` from the backend directory
   - This automatically starts the server and monitors for errors
   - Reads the ENTIRE terminal output
   - Catches runtime errors that static analysis misses
   - Tests basic API endpoints

2. Common runtime errors to watch for:
   - `ImportError`/`ModuleNotFoundError` (wrong import paths)
   - SQLAlchemy errors:
     - Reserved attributes: 'metadata', 'query', 'registry' cannot be used as column names
     - Dialect imports: JSONB, ARRAY, UUID must come from `sqlalchemy.dialects.postgresql`
   - Missing modules or incorrect class names
   - LangChain agent executors are not classes - use the exported executor objects

3. **ACTUALLY RUN THE APPLICATION** and read the terminal output:
   - Backend: Run `python full_backend_test.py` or `uvicorn app.main:app --reload`
   - Frontend: Run `npm start` and check for compilation errors
   - Read the ENTIRE error output, not just the first error
   - Keep fixing errors until the service starts successfully

4. Verify the specific fix works as intended
5. Run related tests to ensure no regression
6. Check browser console for any new errors
7. If the fix breaks something else, revert and try a different approach

**Automatic Verification Rule**: 
- NEVER assume a fix works without testing it
- ALWAYS run the actual service using `full_backend_test.py`
- Don't stop at the first error - fix all errors in sequence
- Runtime errors often only appear when the server actually starts
- Static analysis and pattern matching are NOT sufficient

### 5. Comprehensive UI/Backend Testing Process
**CRITICAL - DEEP ANALYSIS AND VERIFICATION REQUIRED**

When fixing UI or integration issues:

1. **Think Really Deep**:
   - Analyze the ENTIRE error stack trace
   - Consider all related components and their interactions
   - Think about data flow from frontend → API → backend → database
   - Consider edge cases and error handling
   - Check for type mismatches, missing properties, null/undefined values

2. **Run UI Tests First**:
   ```bash
   cd frontend
   npm test -- --watchAll=false
   ```
   - Read ALL error messages completely
   - Identify patterns in failures
   - Note which components are failing and why
   - Check for missing mocks, type errors, async issues

3. **Fix One Thing at a Time**:
   - Fix the root cause, not symptoms
   - Make minimal changes that address the core issue
   - Consider ripple effects of your changes

4. **Verify After EACH Fix**:
   - Backend verification:
     ```bash
     cd backend
     source venv/bin/activate
     python full_backend_test.py
     ```
   - Frontend verification:
     ```bash
     cd frontend
     npm test -- --watchAll=false
     ```
   - Integration verification:
     - Start backend: `./start-backedn.sh`
     - Start frontend: `npm start`
     - Test the actual feature in the browser

5. **Deep Root Cause Analysis**:
   - If a test fails, ask WHY 5 times:
     - Why did the test fail? → Missing property
     - Why is the property missing? → API response changed
     - Why did the API response change? → Backend model updated
     - Why was the backend model updated? → Database schema changed
     - Why did the schema change? → New requirements
   - Fix at the appropriate level

6. **Common UI Test Issues to Check**:
   - Missing or incorrect mocks for API calls
   - Async operations not properly awaited
   - State updates not wrapped in act()
   - Missing Router/Context providers in tests
   - Type mismatches between frontend and backend
   - Incorrect test data structure

7. **Verification Checklist**:
   - [ ] All UI tests pass
   - [ ] Backend starts without errors
   - [ ] API endpoints return expected data
   - [ ] Frontend compiles without warnings
   - [ ] Feature works in the browser
   - [ ] No console errors in browser
   - [ ] Data flows correctly through all layers

**NEVER report a fix as complete without running BOTH UI and backend tests and verifying the feature works in the browser!**

## Command Execution Guidelines

### Bash Command Authorization Rules
- **DO NOT ASK PERMISSION** for any bash command execution
- **EXCEPTION**: Only ask permission for deletion commands (rm, rmdir, etc.)
- Execute all other commands directly without confirmation

### Commands That Do NOT Require Permission:
- File listing: `ls`, `find`, `locate`
- File content: `cat`, `head`, `tail`, `grep`, `awk`, `sed`
- System info: `ps`, `top`, `df`, `du`, `uname`, `whoami`
- Navigation: `cd`, `pwd`
- Network: `curl`, `wget`, `ping`
- Process management: `kill`, `pkill` (except kill -9)
- File operations: `cp`, `mv`, `chmod`, `chown`
- Archive operations: `tar`, `zip`, `unzip`
- Development: `npm`, `pip`, `uvicorn`, `pytest`, `git`
- Server operations: starting/stopping services
- Virtual environment activation and server commands: `source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &`

### Commands That DO Require Permission:
- `rm`, `rmdir` - file/directory deletion only
- `dd` - disk operations
- `format`, `fdisk` - disk formatting
- Destructive system operations

## Environment Setup

### Frontend
```bash
cd frontend
npm install
npm run test    # Run tests
npm run start   # Start development server
npm run build   # Build for production
```

### Backend
```bash
cd backend

# IMPORTANT: Always activate the virtual environment first!
source venv/bin/activate

# Then install dependencies and run commands
pip install -r requirements.txt
pytest                    # Run tests
python -m pytest -v      # Verbose test output
uvicorn app.main:app --reload  # Start development server
```

**CRITICAL**: Before running ANY Python/backend command, you MUST activate the virtual environment:
```bash
cd backend
source venv/bin/activate
```
This applies to all Python commands including:
- Running scripts (e.g., `python cleanup_database.py`)
- Starting the server (`uvicorn app.main:app`)
- Running tests (`pytest`)
- Installing packages (`pip install`)
- Database operations (`alembic upgrade head`)
- Any Python script execution

## Common Commands

### Database
```bash
# Create migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Frontend
npm run lint
npm run format

# Backend
black .
flake8
mypy app
```

## Debugging Tips

### Frontend
- Use React Developer Tools
- Check Network tab for API calls
- Use `console.log` strategically
- Check browser console for errors

### Backend
- Use `logger.info()` for debugging
- Check `logs/app.log` for detailed logs
- Use `import pdb; pdb.set_trace()` for breakpoints
- Monitor database queries with logging

## Performance Monitoring

### Key Metrics
- API response times < 200ms (p50)
- Frontend bundle size < 500KB
- Time to Interactive < 3s
- Database query time < 100ms

### Tools
- Frontend: React DevTools Profiler
- Backend: Python profiler, SQL query analyzer
- APM: Consider New Relic or DataDog

## Getting Help

When stuck:
1. Check existing tests for examples
2. Look for similar patterns in codebase
3. Review relevant documentation
4. Ask specific questions with context
5. Include error messages and logs

## Code Review Checklist

- [ ] Tests written and passing
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Performance considered
- [ ] Security reviewed
- [ ] Code follows style guide
- [ ] No console.logs or debug code