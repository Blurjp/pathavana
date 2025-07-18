const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to trace sendMessageNonStreaming execution
 */
async function debugSendMessage() {
  console.log('🔍 Debug sendMessageNonStreaming Test');
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
    
    // Inject debugging code before login
    await driver.executeScript(`
      // Override console.log to capture logs
      window.debugLogs = [];
      const originalLog = console.log;
      console.log = function(...args) {
        window.debugLogs.push(args.join(' '));
        originalLog.apply(console, args);
      };
      
      // Add debugging to fetch
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = args[0];
        console.log('FETCH:', url);
        
        const response = await originalFetch.apply(this, args);
        
        if (url.includes('/api/v1/travel/sessions')) {
          const clonedResponse = response.clone();
          const data = await clonedResponse.json();
          console.log('API Response for', url, ':', JSON.stringify(data));
          
          if (data.data) {
            console.log('Response has data.message:', 'message' in data.data);
            console.log('Response has data.initial_response:', 'initial_response' in data.data);
            if (data.data.initial_response) {
              console.log('initial_response value:', data.data.initial_response);
            }
          }
        }
        
        return response;
      };
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
    
    // Clear logs
    await driver.executeScript('window.debugLogs = [];');
    
    // Find chat input
    await driver.sleep(2000);
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, I need help planning a trip');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get debug logs
    const logs = await driver.executeScript('return window.debugLogs || [];');
    console.log('\n📋 Debug Logs:');
    console.log('─'.repeat(40));
    
    // Filter relevant logs
    logs.forEach(log => {
      if (log.includes('API Response') || 
          log.includes('initial_response') || 
          log.includes('message in') ||
          log.includes('Session created') ||
          log.includes('New session created')) {
        console.log(log);
      }
    });
    
    // Check displayed message
    const messages = await driver.findElements(By.css('.message-content'));
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 Displayed AI Response:`);
      console.log('─'.repeat(40));
      console.log(lastMessage);
    }
    
    console.log('\n✅ Debug test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
debugSendMessage().catch(console.error);