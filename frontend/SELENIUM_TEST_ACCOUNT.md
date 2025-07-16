# Selenium Test Account Setup

## ✅ Test Account Created

A dedicated test account has been created for all Selenium UI tests:

### Credentials
```
Email:    selenium.test@example.com
Password: SeleniumTest123!
Name:     Selenium Test User
```

## Setup Instructions

### 1. Create Test User (Backend)
```bash
cd backend
source venv/bin/activate
python create_selenium_test_user.py
```

This script:
- Creates the test user if it doesn't exist
- Updates the password if user already exists
- Ensures the user is active and verified
- Tests that login works

### 2. Verify Test User
```bash
cd backend
source venv/bin/activate
python verify_test_user.py
```

This will test the login and show if authentication is working.

## Running Tests with Authentication

### Option 1: Updated Trip Plan Test (Recommended)
```bash
cd frontend
npm run test:v2
```

This uses the new `TripPlanTestV2.js` which:
- Uses centralized test configuration
- Has the correct test credentials
- Better error handling and screenshots

### Option 2: Original Trip Plan Test
```bash
cd frontend
npm run test:trip-plan
```

Updated to use the new credentials.

### Option 3: Simple Test
```bash
cd frontend
npm run test:simple
```

Good for debugging - shows step-by-step what's happening.

## Test Configuration

All test settings are centralized in:
```
frontend/src/tests/e2e/testConfig.js
```

This includes:
- Test user credentials
- URLs
- Timeouts
- CSS selectors
- Chrome options

## What the Tests Do

1. **Navigate to Homepage** - Goes to http://localhost:3000
2. **Login** - Clicks Sign In and enters test credentials
3. **Navigate to Chat** - Goes to the chat page
4. **Send Travel Request** - Types and sends a travel planning message
5. **Wait for AI Response** - Waits up to 90 seconds for AI to respond
6. **Verify Trip Plan** - Checks that the trip plan is displayed

## Troubleshooting

### "Cannot find Sign In button"
- User might already be logged in
- Clear browser cookies/localStorage
- Or use incognito mode

### "Login failed"
- Ensure backend is running on port 8001
- Run `verify_test_user.py` to check authentication
- Check backend logs for errors

### "Timeout waiting for AI response"
- Check backend AI service is running
- Ensure all required API keys are configured
- Check backend logs for errors

## Manual Testing

You can also manually test with these credentials:
1. Go to http://localhost:3000
2. Click "Sign In"
3. Enter:
   - Email: selenium.test@example.com
   - Password: SeleniumTest123!
4. Navigate to Chat
5. Send a travel request

## Next Steps

The test account is now ready and all Selenium tests have been updated to use it. You can run any of the test commands above to verify the complete flow of:
- User authentication
- Chat navigation
- Travel plan creation via AI agent
- Trip plan display verification