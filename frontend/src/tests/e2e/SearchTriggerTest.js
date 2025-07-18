const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to verify search triggering
 */
async function searchTriggerTest() {
  console.log('🔍 Search Trigger Test');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  // Enable browser logs
  const prefs = new logging.Preferences();
  prefs.setLevel(logging.Type.BROWSER, logging.Level.ALL);
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .setLoggingPrefs(prefs)
    .build();
  
  try {
    // Navigate
    await driver.get('http://localhost:3000');
    await driver.sleep(2000);
    
    // Clear storage
    await driver.executeScript(`
      localStorage.clear();
      sessionStorage.clear();
    `);
    
    // Login
    console.log('🔐 Logging in...');
    const signInButton = await driver.findElement(By.css('.auth-buttons button:first-child'));
    await signInButton.click();
    await driver.sleep(1000);
    
    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    await emailInput.sendKeys('selenium.test@example.com');
    
    const passwordInput = await driver.findElement(By.css('input[type="password"]'));
    await passwordInput.sendKeys('SeleniumTest123!');
    
    const submitButton = await driver.findElement(By.css('button[type="submit"]'));
    await submitButton.click();
    
    // Wait for auth
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully');
    
    await driver.sleep(2000);
    
    // Find chat input
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      10000
    );
    console.log('✅ Found chat input');
    
    // Send a message that should trigger searches
    console.log('\n📝 Sending search-triggering message...');
    await chatInput.clear();
    await chatInput.sendKeys('I want to fly from New York to Paris next week');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait longer for potential search processing
    console.log('\n⏳ Waiting for AI response and potential searches...');
    await driver.sleep(8000);
    
    // Check messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Messages displayed: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 AI Response:`);
      console.log(lastMessage);
      
      // Check if response mentions searches or lacks dates
      if (lastMessage.includes('search') || lastMessage.includes('flight') || lastMessage.includes('date')) {
        console.log('\n✅ AI acknowledged the flight request');
      }
    }
    
    // Get console logs to check for search activity
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Search-related logs:');
    logs.forEach(entry => {
      if (entry.message.includes('search') || entry.message.includes('Search')) {
        console.log(entry.message);
      }
    });
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
searchTriggerTest().catch(console.error);