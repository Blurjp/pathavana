const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to capture console logs
 */
async function consoleLogTest() {
  console.log('🔍 Console Log Test');
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
    
    // Clear logs
    await driver.manage().logs().get(logging.Type.BROWSER);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Test message');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait briefly
    await driver.sleep(2000);
    
    // Get console logs
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Console Logs:');
    console.log('─'.repeat(40));
    
    logs.forEach(entry => {
      const msg = entry.message;
      if (msg.includes('[useChatManager]') || msg.includes('sendMessage')) {
        console.log(msg);
      }
    });
    
    // Check if no relevant logs
    const relevantLogs = logs.filter(entry => 
      entry.message.includes('[useChatManager]') || entry.message.includes('sendMessage')
    );
    
    if (relevantLogs.length === 0) {
      console.log('❌ No useChatManager logs found!');
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
consoleLogTest().catch(console.error);