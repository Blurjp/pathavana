# Trip Plan Creation UI Test

## Overview
This is a comprehensive Selenium UI test that validates the complete user journey of creating a travel plan through the AI chat interface in Pathavana.

## Test Flow

### 1. User Authentication
- Opens the application homepage
- Clicks "Sign In" button
- Enters test credentials
- Verifies successful login via user avatar

### 2. Navigation to Chat
- Navigates to the chat page
- Verifies chat interface is loaded
- Confirms chat input is available

### 3. Travel Request Submission
- Types a detailed travel request:
  ```
  Create a comprehensive 5-day travel plan to Tokyo, Japan. 
  I'm flying from San Francisco. Please include flight options, 
  hotel recommendations in Shibuya area, and a daily itinerary 
  with must-see attractions, local restaurants, and cultural 
  experiences. My budget is around $3000 per person.
  ```
- Sends the message to the AI agent

### 4. AI Response Generation
- Waits for the AI to process the request
- Monitors for travel plan generation
- Verifies response contains travel content

### 5. Trip Plan Verification
- Checks for trip plan display in the UI
- Verifies key components:
  - ✅ Day-by-day itinerary
  - ✅ Flight information
  - ✅ Hotel recommendations
  - ✅ Attractions mentioned
  - ✅ Restaurant suggestions
  - ✅ Budget information

## Running the Test

### Prerequisites
1. **Chrome Browser** installed
2. **Frontend** running on http://localhost:3000
3. **Backend** running on http://localhost:8001
4. **Test user** account created

### Quick Start
```bash
# Run with automatic setup checks
npm run test:trip-plan-full

# Or run directly
npm run test:trip-plan
```

### Manual Execution
```bash
# 1. Ensure servers are running
npm start                    # Frontend (in one terminal)
cd backend && uvicorn app.main:app --reload --port 8001  # Backend (in another terminal)

# 2. Run the test
node src/tests/e2e/TripPlanCreationTest.js
```

## Test Output Example

```
🚀 Trip Plan Creation UI Test
════════════════════════════════════════════════════════════
📍 Target: http://localhost:3000
🕐 Started: 7/15/2025, 9:30:00 PM
📁 Screenshots: src/tests/e2e/screenshots/test-run-1234567890
════════════════════════════════════════════════════════════

🔐 Step 1: User Authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🔍 Finding Sign In button...
   ✅ Clicked Sign In button
   ⏳ Waiting for login modal...
   ✅ Entered email
   ✅ Entered password
   ✅ Submitted login form
   ⏳ Waiting for authentication...
   ✅ Authentication successful!
   📸 Screenshot: 01-logged-in.png

📍 Step 2: Navigate to Chat
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📍 Current URL: http://localhost:3000/
   🔍 Looking for Chat navigation link...
   ✅ Clicked Chat link
   ✅ Successfully on chat page
   📸 Screenshot: 02-chat-page.png

💬 Step 3: Send Travel Planning Request
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🔍 Looking for chat input field...
   ✅ Found chat input: textarea
   📝 Typing travel request...
   📸 Screenshot: 03-message-typed.png
   🚀 Sending message...
   ✅ Clicked send button
   ✅ Travel request sent successfully!

🤖 Step 4: Wait for AI Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ⏳ Waiting for AI to generate travel plan...
   ⏱️  5 seconds elapsed...
   ⏱️  10 seconds elapsed...
   ✅ AI response received!
   📄 Response preview: Day 1: Arrival in Tokyo...
   ⏱️  Total response time: 12 seconds
   📸 Screenshot: 04-ai-response.png

📋 Step 5: Verify Trip Plan Display
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🔍 Looking for trip plan display...
   📂 Opening sidebar...
   ✅ Found trip plan in: .trip-plan-panel

   📊 Trip Plan Analysis:
   ────────────────────────────────────────
   ✅ Day-by-day itinerary
   ✅ Flight information
   ✅ Hotel recommendations
   ✅ Attractions mentioned
   ✅ Restaurant suggestions
   ✅ Budget information

   📄 Content Sample:
   ────────────────────────────────────────
   Day 1: Arrive at Narita Airport, take the Narita Express to Tokyo Station...
   Flights: United Airlines UA837 departing SFO at 11:30 AM...
   📸 Screenshot: 05-trip-plan-displayed.png

   ✅ Trip plan successfully created and displayed!

✅ TEST PASSED - All Steps Completed Successfully!
════════════════════════════════════════════════════════════
📊 Summary:
   ✅ User authentication successful
   ✅ Navigation to chat page working
   ✅ Travel request sent to AI agent
   ✅ AI generated comprehensive travel plan
   ✅ Trip plan displayed in UI
════════════════════════════════════════════════════════════
📸 Screenshot: 06-test-success.png

🏁 Test completed: 7/15/2025, 9:30:45 PM
📸 Screenshots saved to: src/tests/e2e/screenshots/test-run-1234567890
```

## Screenshots

The test captures screenshots at key points:

1. **01-logged-in.png** - After successful authentication
2. **02-chat-page.png** - Chat interface loaded
3. **03-message-typed.png** - Travel request typed in input
4. **04-ai-response.png** - AI response received
5. **05-trip-plan-displayed.png** - Trip plan shown in UI
6. **06-test-success.png** - Final success state

Error screenshots are also captured if any step fails.

## Test User Setup

The test uses the following credentials:
- Email: `test@example.com`
- Password: `testpassword`

To create the test user:
```bash
node src/tests/e2e/setupTestUser.js
```

Or use the Python script:
```bash
cd backend
source venv/bin/activate
python create_test_user.py
```

## Customization

### Different Travel Requests
Edit the `travelRequest` variable in `TripPlanCreationTest.js`:

```javascript
const travelRequest = "Your custom travel request here...";
```

### Timeout Configuration
Adjust timeouts for slower systems:

```javascript
const timeout = 90000; // 90 seconds for AI response
```

### Headless Mode
Run without browser window:

```javascript
options.addArguments('--headless');
```

## Troubleshooting

### Test user login fails
1. Ensure test user exists in database
2. Check backend logs for authentication errors
3. Verify correct credentials in test

### AI response timeout
1. Check backend AI service is running
2. Increase timeout value
3. Verify API endpoints are responding

### Trip plan not found
1. Check sidebar toggle functionality
2. Verify CSS selectors match current UI
3. Check browser console for errors

### Screenshots not saved
1. Ensure write permissions for screenshots directory
2. Check disk space
3. Verify path exists

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Trip Plan UI Test
  run: |
    npm run test:trip-plan-full
  env:
    CHROME_BIN: /usr/bin/google-chrome
```

### Jenkins
```groovy
stage('UI Tests') {
  steps {
    sh 'npm run test:trip-plan-full'
  }
}
```

## Debugging

Enable verbose logging:
```javascript
// Add to test file
console.log(await this.driver.getPageSource()); // Full HTML
console.log(await this.driver.getCurrentUrl()); // Current URL
console.log(await element.getAttribute('class')); // Element details
```

## Next Steps

1. Add more test scenarios (different destinations, budgets)
2. Test error cases (invalid requests, network failures)
3. Add performance benchmarks
4. Create visual regression tests
5. Test mobile responsive behavior