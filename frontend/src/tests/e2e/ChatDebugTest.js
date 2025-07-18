const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to check console logs and network errors
 */
async function chatDebugTest() {
  console.log('🔍 Chat Debug Test');
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
    // Navigate and login
    await driver.get('http://localhost:3000');
    await driver.sleep(2000);
    
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
    
    // Clear console logs
    await driver.manage().logs().get(logging.Type.BROWSER);
    
    // Find chat input
    await driver.sleep(2000);
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, I need help planning a trip to Paris');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get console logs
    console.log('\n📋 Browser Console Logs:');
    console.log('─'.repeat(40));
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    logs.forEach(entry => {
      const msg = entry.message;
      if (msg.includes('SSE') || msg.includes('EventSource') || msg.includes('error') || msg.includes('stream')) {
        console.log(`[${entry.level.name}] ${msg}`);
      }
    });
    
    // Check for messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Found ${messages.length} messages`);
    
    // Print last AI message
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 Last AI Response:`);
      console.log('─'.repeat(40));
      console.log(lastMessage.substring(0, 200) + '...');
    }
    
    // Check session storage
    const sessionData = await driver.executeScript("return window.sessionStorage.getItem('pathavana_session_id');");
    console.log(`\n🔑 Session ID: ${sessionData}`);
    
    // Check if EventSource is being used
    const hasEventSource = await driver.executeScript("return typeof EventSource !== 'undefined';");
    console.log(`📡 EventSource supported: ${hasEventSource}`);
    
    console.log('\n✅ Debug test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
chatDebugTest().catch(console.error);