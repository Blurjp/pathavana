const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Selenium UI Test to verify date picker fixes
 * Tests: 1. Quick date options working 2. Context detection 3. UI size fixes 4. Trip plan creation
 */
async function testDatePickerFixes() {
  console.log('🗓️ Date Picker Fixes Verification Test');
  console.log('════════════════════════════════════════════════════════════');
  
  let driver;
  
  try {
    // Setup Chrome driver
    const options = new chrome.Options();
    options.addArguments('--window-size=1920,1080');
    options.addArguments('--disable-dev-shm-usage');
    options.addArguments('--no-sandbox');
    
    driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();

    console.log('🔐 Logging in...');
    await driver.get('http://localhost:3000');
    
    // Login process
    await driver.wait(until.elementLocated(By.css('button, a')), 10000);
    
    const signInButton = await driver.findElement(By.xpath("//button[contains(text(), 'Sign In') or contains(text(), 'Login')]"));
    await signInButton.click();
    
    await driver.wait(until.elementLocated(By.css('input[type="email"], input[name="email"]')), 5000);
    
    const emailInput = await driver.findElement(By.css('input[type="email"], input[name="email"]'));
    await emailInput.sendKeys('test@pathavana.com');
    
    const passwordInput = await driver.findElement(By.css('input[type="password"], input[name="password"]'));
    await passwordInput.sendKeys('password123');
    
    const loginButton = await driver.findElement(By.css('button[type="submit"]'));
    await loginButton.click();
    
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully');

    // Test 1: Trigger date picker with travel dates question
    console.log('\n📝 Test 1: Date Picker Context Detection');
    console.log('────────────────────────────────────────');
    
    const chatInput = await driver.wait(until.elementLocated(By.css('textarea, input[type="text"]')), 10000);
    await chatInput.clear();
    await chatInput.sendKeys('When would you like to travel?');
    
    const sendButton = await driver.findElement(By.css('button[type="submit"]'));
    await sendButton.click();
    
    // Wait for AI response that should trigger date picker
    await driver.sleep(5000);
    
    // Look for date picker component
    try {
      const dateChips = await driver.wait(until.elementLocated(By.css('.compact-date-chips, .date-chips-grid')), 10000);
      console.log('  ✅ Date picker appeared after date question');
      
      // Check if it's compact (smaller size)
      const chipRect = await dateChips.getRect();
      console.log(`  📏 Date picker width: ${chipRect.width}px (should be ≤400px)`);
      
      if (chipRect.width <= 400) {
        console.log('  ✅ Date picker is compact (≤400px width)');
      } else {
        console.log('  ❌ Date picker is too wide (>400px)');
      }
      
      // Test 2: Check quick date options are clickable
      console.log('\n📝 Test 2: Quick Date Options Functionality');
      console.log('────────────────────────────────────────');
      
      const todayButton = await driver.findElement(By.xpath("//button[contains(text(), 'Today')]"));
      console.log('  ✅ Found "Today" quick option');
      
      const tomorrowButton = await driver.findElement(By.xpath("//button[contains(text(), 'Tomorrow')]"));
      console.log('  ✅ Found "Tomorrow" quick option');
      
      const weekendButton = await driver.findElement(By.xpath("//button[contains(text(), 'This Weekend')]"));
      console.log('  ✅ Found "This Weekend" quick option');
      
      // Click on "Today" option
      await todayButton.click();
      console.log('  🖱️ Clicked "Today" option');
      
      // Wait and check if a message was sent
      await driver.sleep(2000);
      
      const messages = await driver.findElements(By.css('.message, .chat-message'));
      const lastMessage = messages[messages.length - 1];
      const messageText = await lastMessage.getText();
      
      if (messageText.includes('want to') && (messageText.includes('today') || messageText.includes('travel'))) {
        console.log('  ✅ Quick date option successfully sent message');
        console.log(`  📨 Message: "${messageText}"`);
      } else {
        console.log('  ❌ Quick date option did not send expected message');
      }
      
    } catch (error) {
      console.log('  ❌ Date picker not found or not working');
      console.log(`  Error: ${error.message}`);
    }

    // Test 3: Test flight vs hotel context detection
    console.log('\n📝 Test 3: Context Detection (Flight vs Hotel)');
    console.log('────────────────────────────────────────');
    
    // Test flight context
    await chatInput.clear();
    await chatInput.sendKeys('When would you like to depart on your flight?');
    await sendButton.click();
    await driver.sleep(3000);
    
    try {
      const flightContext = await driver.findElement(By.xpath("//span[contains(text(), 'Departure') and contains(text(), 'Return')]"));
      console.log('  ✅ Flight context detected (Departure & Return)');
    } catch (error) {
      console.log('  ❌ Flight context not detected');
    }
    
    // Close any existing date picker
    try {
      const closeButton = await driver.findElement(By.css('button[aria-label*="Close"], .close-chips-btn'));
      await closeButton.click();
      await driver.sleep(1000);
    } catch (e) {
      // No close button found, continue
    }
    
    // Test hotel context
    await chatInput.clear();
    await chatInput.sendKeys('When would you like to check in to your hotel?');
    await sendButton.click();
    await driver.sleep(3000);
    
    try {
      const hotelContext = await driver.findElement(By.xpath("//span[contains(text(), 'Check-in') and contains(text(), 'Check-out')]"));
      console.log('  ✅ Hotel context detected (Check-in & Check-out)');
    } catch (error) {
      console.log('  ❌ Hotel context not detected');
    }

    // Test 4: Trip plan creation
    console.log('\n📝 Test 4: Trip Plan Creation');
    console.log('────────────────────────────────────────');
    
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan travel to Paris');
    await sendButton.click();
    
    // Wait for response
    await driver.sleep(8000);
    
    // Check if sidebar opens or trip plan is created
    try {
      const sidebar = await driver.findElement(By.css('.search-results-sidebar, .sidebar'));
      console.log('  ✅ Sidebar exists');
      
      const tripPlanTab = await driver.findElement(By.xpath("//button[contains(text(), 'Trip Plan')]"));
      console.log('  ✅ Trip Plan tab found');
      
      await tripPlanTab.click();
      await driver.sleep(2000);
      
      const tripPlanContent = await driver.findElements(By.css('.enhanced-trip-plan-panel, .trip-plan-panel'));
      if (tripPlanContent.length > 0) {
        console.log('  ✅ Trip Plan panel opened successfully');
      } else {
        console.log('  ⚠️ Trip Plan panel not found (may be empty)');
      }
      
    } catch (error) {
      console.log('  ❌ Trip plan creation or sidebar not working');
      console.log(`  Error: ${error.message}`);
    }

    console.log('\n✅ Date Picker Fixes Test Completed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    if (driver) {
      await driver.quit();
    }
  }
}

// Run the test
testDatePickerFixes().catch(console.error);