const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to find why chat API calls are not being made
 */
async function chatErrorTest() {
  console.log('🔍 Chat Error Test');
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
    
    // Add error tracking
    await driver.executeScript(`
      window.errors = [];
      window.addEventListener('error', (e) => {
        window.errors.push({
          message: e.message,
          filename: e.filename,
          line: e.lineno,
          col: e.colno
        });
      });
      
      // Track console errors
      const originalError = console.error;
      console.error = function(...args) {
        window.errors.push({
          type: 'console.error',
          message: args.join(' ')
        });
        originalError.apply(console, args);
      };
      
      // Track fetch errors
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        console.log('FETCH CALLED:', args[0]);
        try {
          const response = await originalFetch.apply(this, args);
          if (!response.ok) {
            window.errors.push({
              type: 'fetch_error',
              url: args[0],
              status: response.status
            });
          }
          return response;
        } catch (e) {
          window.errors.push({
            type: 'fetch_exception',
            url: args[0],
            error: e.message
          });
          throw e;
        }
      };
    `);
    
    await driver.sleep(2000);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Try to trigger all the chat logic
    console.log('\n📝 Testing chat send logic...');
    
    // First, check if sendMessage function exists
    const hasSendMessage = await driver.executeScript(`
      // Try to find the chat component and its sendMessage function
      const textarea = document.querySelector('textarea[placeholder*="travel"]');
      const reactKey = Object.keys(textarea).find(key => key.startsWith('__react'));
      const reactInstance = textarea[reactKey];
      
      // Try to trace up to find the component with sendMessage
      let node = reactInstance;
      let found = false;
      let depth = 0;
      
      while (node && depth < 20) {
        if (node.memoizedProps && node.memoizedProps.onSendMessage) {
          found = true;
          break;
        }
        if (node.return) {
          node = node.return;
        } else {
          break;
        }
        depth++;
      }
      
      return {
        found: found,
        depth: depth,
        hasTextarea: !!textarea,
        hasReactInstance: !!reactInstance
      };
    `);
    
    console.log('SendMessage function check:', hasSendMessage);
    
    // Send message
    await chatInput.clear();
    await chatInput.sendKeys('Hello, I need help');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait and check for errors
    await driver.sleep(3000);
    
    // Get errors
    const errors = await driver.executeScript('return window.errors || [];');
    console.log('\n❌ Errors found:', errors.length);
    errors.forEach((err, i) => {
      console.log(`\nError ${i + 1}:`, err);
    });
    
    // Get console logs
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Browser logs with errors/warnings:');
    logs.forEach(entry => {
      if (entry.level.name === 'SEVERE' || entry.level.name === 'WARNING' || entry.message.includes('error')) {
        console.log(`[${entry.level.name}] ${entry.message}`);
      }
    });
    
    // Check what happened with the message
    const messageInfo = await driver.executeScript(`
      const messages = Array.from(document.querySelectorAll('.message-content'));
      return {
        messageCount: messages.length,
        lastMessage: messages[messages.length - 1]?.innerText || null,
        inputValue: document.querySelector('textarea[placeholder*="travel"]').value
      };
    `);
    
    console.log('\n📨 Message Info:', messageInfo);
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
chatErrorTest().catch(console.error);