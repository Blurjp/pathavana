# Manual Test: Trip Plan Creation Feature

## Test Scenario: AI Agent Auto-Creates Trip Plan

### Steps to Test:

1. **Start the Application**
   - Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001`
   - Frontend: `cd frontend && npm start`

2. **Navigate to Chat Interface**
   - Open browser to http://localhost:3000/chat
   - A new session should be created automatically

3. **Test Trip Plan Creation Intent**
   - Type one of these messages:
     - "Create a trip plan to Paris for next week"
     - "Help me plan my vacation to Tokyo"
     - "I want to build my itinerary for London"
     - "Start planning my trip to Rome"

4. **Expected Behavior**
   - AI agent should respond acknowledging the trip plan creation
   - The response metadata should include `trip_plan_created: true`
   - The sidebar should open automatically
   - The "Trip Plan" tab should be visible in the sidebar
   - The trip plan should show the destination mentioned

5. **Verify Backend Processing**
   - Check backend logs for: "🎯 Trip plan creation intent detected"
   - Check for: "✅ Trip plan created: Trip to [destination]"

6. **Test Adding Items to Trip Plan**
   - After trip plan is created, search for flights: "Find flights to [destination]"
   - When results appear, click "Add to Trip" on any flight
   - The item should appear in the Trip Plan panel

## Test Cases

### ✅ Positive Cases:
1. Explicit trip plan creation phrases
2. Trip plan with full details (destination, dates, travelers)
3. Trip plan with partial information
4. Adding search results to trip plan

### ❌ Negative Cases:
1. General travel questions without planning intent
2. Search queries without trip plan context
3. Multiple trip plan creation attempts (should not duplicate)

## Debugging

If trip plan is not created:
1. Check browser console for errors
2. Check network tab for API responses
3. Look for `metadata.should_create_trip_plan` in chat response
4. Verify backend trip_context_service.py has the detect_trip_plan_intent method

## Success Criteria
- [ ] Trip plan intent is detected correctly
- [ ] Trip plan is created in session plan_data
- [ ] Sidebar opens automatically
- [ ] Trip plan information is displayed correctly
- [ ] Can add items to the trip plan