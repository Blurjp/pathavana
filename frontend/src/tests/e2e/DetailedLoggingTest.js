const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to capture detailed logging from useChatManager
 */
async function detailedLoggingTest() {
  console.log('🔍 Detailed Logging Test');
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
    
    // Clear console logs
    await driver.manage().logs().get(logging.Type.BROWSER);
    
    // Wait for and find chat input
    console.log('⏳ Waiting for chat input...');
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea[placeholder*="Continue"], textarea[placeholder*="trip"], textarea')),
      10000
    );
    await driver.wait(until.elementIsVisible(chatInput), 5000);
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello test');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(3000);
    
    // Get console logs
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 All Console Logs:');
    console.log('─'.repeat(40));
    
    logs.forEach(entry => {
      const msg = entry.message;
      // Show all logs that contain useChatManager or response processing
      if (msg.includes('[useChatManager]') || 
          msg.includes('Processing response') ||
          msg.includes('Has message') ||
          msg.includes('Has initial_response') ||
          msg.includes('Final responseContent')) {
        console.log(msg);
      }
    });
    
    // Check messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Messages displayed: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 AI Response: "${lastMessage}"`);
    }
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
detailedLoggingTest().catch(console.error);