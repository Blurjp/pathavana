# Manual Test for New Chat Functionality

## Test Steps

1. **Open the application**
   - Navigate to http://localhost:3000
   - You should see the Pathavana travel planning interface

2. **Click "New Chat" button**
   - Look for the "➕ New Chat" button in the chat header
   - Click it

3. **Expected Result**
   - A new session should be created
   - You should see an initial conversation with:
     - User message: "Hello, I want to plan a trip"
     - Assistant response: "I'd be happy to help you plan your trip! I can assist you with finding flights, hotels, and activities. Could you tell me more about where you'd like to go and when?"
   - The chat should be ready for you to type your next message

4. **Verify in Browser Console**
   - Open browser developer tools (F12)
   - Check the console for:
     - "Messages in UnifiedTravelRequest: 2" (showing 2 initial messages)
     - No errors about missing messages or undefined properties

5. **Check LocalStorage**
   - In browser developer tools, go to Application/Storage tab
   - Look for LocalStorage entries:
     - `currentSessionId` - should have a UUID
     - `pathavana_messages_[sessionId]` - should have 2 messages

## API Test

You can also test the API directly:

```bash
curl -X POST http://localhost:8001/api/v1/travel/sessions \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I want to plan a trip", "source": "web"}' \
  | python -m json.tool
```

Expected response:
```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "initial_response": "I'd be happy to help you plan your trip!...",
    "metadata": {
      "hints": [...],
      ...
    }
  }
}
```

## Summary of Changes Made

1. **Fixed TypeScript type definition** in `unifiedTravelApi.ts`:
   - Updated `createSession` return type to include `initial_response` field
   - This matches what the backend actually returns

2. **Fixed property access** in `useSessionManager.ts`:
   - Changed from checking both `initial_response` and `initialResponse`
   - Now only uses `initial_response` (snake_case) as returned by backend

3. **Initial messages are created** when a new session starts:
   - User's initial message
   - Assistant's initial response with metadata/hints

4. **Messages are saved to localStorage** immediately:
   - Using the key `pathavana_messages_${sessionId}`
   - This ensures the chat UI loads with the initial conversation

The fix ensures that when users click "New Chat", they immediately see the conversation starter instead of an empty chat window.