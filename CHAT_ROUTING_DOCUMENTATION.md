# Chat Routing Documentation

## Overview

The Pathavana application uses a URL-based routing system for chat sessions where each chat has a unique ID that is shared with Trip Plans. This ensures consistency between chat conversations and the trip plans created from them.

## URL Structure

### Routes

1. **`/chat`** - New Chat Creation
   - Purpose: Creates a new chat session
   - Behavior: Automatically redirects to `/chat/{sessionId}` after creation
   - Component: `TravelRequest.tsx`

2. **`/chat/{sessionId}`** - Existing Chat Session
   - Purpose: Loads and displays an existing chat session
   - Behavior: Loads messages and context for the specified session
   - Component: `UnifiedTravelRequest.tsx`

3. **`/trips`** - Trip Management
   - Purpose: Lists all saved trips and planning sessions
   - Behavior: Shows tabs for "Saved Trips" and "Planning Sessions"
   - Component: `Trips.tsx`

## Key Implementation Details

### Session ID = Trip Plan ID

The same UUID is used for both:
- Chat session identification
- Trip plan identification

This ensures that when a user creates a trip plan from a chat conversation, they maintain the same ID for easy reference and consistency.

### Navigation Flow

1. **New Chat Flow**:
   ```
   User clicks "New Chat" → Navigate to /chat → Create session → Redirect to /chat/{sessionId}
   ```

2. **Continue Existing Chat**:
   ```
   User clicks "Continue" on Trips page → Navigate to /chat/{sessionId} → Load session
   ```

### Code Examples

#### Creating a New Chat (TravelRequest.tsx)
```typescript
// Redirect to /chat/:sessionId when we have a sessionId
useEffect(() => {
  if (sessionId) {
    navigate(`/chat/${sessionId}`, { replace: true });
  }
}, [sessionId, navigate]);
```

#### Loading Existing Chat (UnifiedTravelRequest.tsx)
```typescript
const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();

// Update URL when sessionId changes
useEffect(() => {
  if (sessionId && sessionId !== urlSessionId) {
    navigate(`/chat/${sessionId}`, { replace: true });
  }
}, [sessionId, urlSessionId, navigate]);
```

#### Linking to Chats (Trips.tsx)
```typescript
<Link to={`/chat/${session.id}`} className="btn-primary">
  Continue
</Link>
```

## API Integration

### Create Session
```bash
POST /api/v1/travel/sessions
Body: {
  "message": "Initial message",
  "source": "web"
}
Response: {
  "session_id": "uuid-here",
  "initial_response": "Assistant's response"
}
```

### Get User Sessions
```bash
GET /api/v1/travel/sessions
Response: [
  {
    "id": "uuid-here",
    "status": "active",
    "messages": [...],
    "context": {...}
  }
]
```

## Testing

Access the test page at: http://localhost:3000/test-chat-routing.html

This page allows you to:
1. Create new sessions via API
2. List all existing sessions
3. Navigate to specific chat sessions
4. Test the routing behavior

## Benefits

1. **Persistent URLs**: Users can bookmark and share specific chat sessions
2. **Browser History**: Back/forward navigation works naturally
3. **Consistent IDs**: Same ID used for chat and trip planning
4. **Clear Navigation**: Users always know which chat they're in via the URL