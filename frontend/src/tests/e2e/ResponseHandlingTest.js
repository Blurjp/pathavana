const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to check response handling
 */
async function responseHandlingTest() {
  console.log('🔍 Response Handling Test');
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
    
    // Add detailed logging to sendMessageNonStreaming
    await driver.executeScript(`
      // Find React fiber to patch the component
      const chatInput = document.querySelector('textarea[placeholder*="travel"]');
      if (chatInput) {
        // Override console.log to capture more details
        const originalLog = console.log;
        window.capturedLogs = [];
        
        console.log = function(...args) {
          window.capturedLogs.push({
            message: args.join(' '),
            timestamp: new Date().toISOString()
          });
          originalLog.apply(console, args);
        };
        
        // Also capture errors
        const originalError = console.error;
        console.error = function(...args) {
          window.capturedLogs.push({
            message: '[ERROR] ' + args.join(' '),
            timestamp: new Date().toISOString(),
            isError: true
          });
          originalError.apply(console, args);
        };
      }
    `);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello test');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get captured logs
    const capturedLogs = await driver.executeScript('return window.capturedLogs || [];');
    
    console.log('\n📋 Captured Logs:');
    console.log('─'.repeat(40));
    
    // Filter for relevant logs
    capturedLogs.forEach(log => {
      if (log.message.includes('sendMessageNonStreaming') || 
          log.message.includes('response') || 
          log.message.includes('data') ||
          log.message.includes('session') ||
          log.isError) {
        console.log(`[${log.timestamp}] ${log.message}`);
      }
    });
    
    // Get browser console logs
    const browserLogs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Browser Console Errors:');
    browserLogs.forEach(entry => {
      if (entry.level.name === 'SEVERE' || entry.message.includes('error')) {
        console.log(`[${entry.level.name}] ${entry.message}`);
      }
    });
    
    // Check final state
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Total messages: ${messages.length}`);
    
    // Check session storage
    const sessionData = await driver.executeScript(`
      return {
        sessionId: localStorage.getItem('pathavana_session_id'),
        hasMessages: !!localStorage.getItem('pathavana_messages_undefined')
      };
    `);
    console.log('\n💾 Session Data:', sessionData);
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
responseHandlingTest().catch(console.error);