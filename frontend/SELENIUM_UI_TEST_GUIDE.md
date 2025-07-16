# Selenium UI Test Guide

## Overview
This guide documents the Selenium UI tests created for testing the chat and travel plan functionality in Pathavana.

## Test Files Created

### 1. `PathavanaUITest.js`
Complete end-to-end test suite that includes:
- Homepage loading
- User authentication
- Navigation to chat
- Sending travel planning requests
- Verifying AI response
- Checking travel plan display in sidebar

### 2. `ChatTravelPlanTest.js`
Focused test for chat functionality:
- Direct chat interaction testing
- Travel plan creation verification
- Handles both authenticated and unauthenticated scenarios

### 3. `TravelPlanUITest.ts`
TypeScript version with comprehensive test coverage and detailed reporting.

## Prerequisites

1. **Chrome Browser**: Must be installed on your system
2. **ChromeDriver**: Automatically installed via npm
3. **Running Application**: 
   - Frontend: `npm start` (http://localhost:3000)
   - Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

## Installation

```bash
# Install Selenium dependencies
npm install --save-dev selenium-webdriver @types/selenium-webdriver chromedriver
```

## Running Tests

### Method 1: NPM Scripts
```bash
# Run the main UI test
npm run test:e2e

# Run the TypeScript version
npm run test:selenium
```

### Method 2: Direct Execution
```bash
# Run specific test file
node src/tests/e2e/PathavanaUITest.js
node src/tests/e2e/ChatTravelPlanTest.js
```

## Test Scenarios Covered

### 1. Authentication Flow
- ✅ Unauthenticated users redirected to homepage
- ✅ Login modal interaction
- ✅ Post-login navigation

### 2. Chat Functionality
- ✅ Finding and interacting with chat input
- ✅ Sending travel planning messages
- ✅ Waiting for AI responses

### 3. Travel Plan Display
- ✅ Checking sidebar/panel visibility
- ✅ Verifying travel plan content
- ✅ Detecting flights, hotels, and itinerary

## Test Output

### Screenshots
- Location: `src/tests/e2e/screenshots/`
- Naming: `{test-name}-{timestamp}.png`
- Captured on errors and successful completions

### Console Output
```
🚀 Pathavana UI Test Suite
══════════════════════════════════════════════════
📍 Target: http://localhost:3000
🕐 Started: 7/15/2025, 9:08:02 PM
══════════════════════════════════════════════════

🧪 Test: Load Homepage
──────────────────────────────────────────────────
✅ PASSED (915ms)

🧪 Test: Send Travel Planning Request
──────────────────────────────────────────────────
💬 Sending message: "Create a 3-day travel plan to Paris..."
✅ Message sent
✅ PASSED (2341ms)

📊 Test Summary
══════════════════════════════════════════════════
Total: 6 | ✅ Passed: 6 | ❌ Failed: 0
Success Rate: 100.0%
```

## Key Features of Tests

### 1. Robust Element Selection
- Multiple selector fallbacks
- Handles dynamic content
- Waits for elements to be visible and enabled

### 2. Smart Waiting
- Configurable timeouts
- Checks for content completion
- Handles loading states

### 3. Comprehensive Verification
- Checks multiple UI areas for travel plans
- Verifies specific content (flights, hotels, itinerary)
- Takes screenshots for visual verification

### 4. Error Handling
- Graceful failures with detailed error messages
- Screenshots on errors
- Continues testing when possible

## Troubleshooting

### Common Issues

1. **"Chrome not found"**
   - Install Chrome browser
   - Ensure Chrome is in system PATH

2. **"Element not found"**
   - Check if UI has changed
   - Increase timeout values
   - Verify selectors match current HTML

3. **"Login failed"**
   - Ensure test user exists in database
   - Check authentication endpoints
   - Verify credentials in test

4. **"Travel plan not displayed"**
   - Check if AI service is running
   - Verify sidebar toggle functionality
   - Ensure proper API responses

## Extending Tests

### Adding New Test Cases
```javascript
async testNewFeature() {
  await this.runTest('Feature Name', async () => {
    // Test implementation
    await this.driver.findElement(By.css('.selector'));
    // Assertions
  });
}
```

### Custom Assertions
```javascript
async verifyTravelPlanDetails() {
  const planText = await this.driver.findElement(By.css('.trip-plan')).getText();
  
  // Check specific details
  if (!planText.includes('Eiffel Tower')) {
    throw new Error('Missing key attraction');
  }
}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Selenium Tests
  run: |
    npm run test:e2e
  env:
    CHROME_BIN: /usr/bin/google-chrome
```

## Best Practices

1. **Keep tests independent**: Each test should be runnable on its own
2. **Use explicit waits**: Avoid sleep() when possible
3. **Take screenshots**: Capture key states for debugging
4. **Clean up**: Always close browser in finally block
5. **Use data-testid**: Add test IDs to make selection easier

## Future Enhancements

1. Add parallel test execution
2. Implement test data management
3. Add visual regression testing
4. Create test reports with Allure or similar
5. Add cross-browser testing support