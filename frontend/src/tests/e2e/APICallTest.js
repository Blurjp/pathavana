const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to verify API calls are being made
 */
async function apiCallTest() {
  console.log('🔍 API Call Test');
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
    
    // Refresh to ensure latest code
    await driver.navigate().refresh();
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
    
    await driver.sleep(2000);
    
    // Inject comprehensive network monitoring
    await driver.executeScript(`
      window.apiCalls = [];
      window.errors = [];
      
      // Monitor fetch
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = args[0];
        const options = args[1] || {};
        
        console.log('[FETCH] Calling:', url);
        
        const callInfo = {
          url: url,
          method: options.method || 'GET',
          body: options.body,
          timestamp: new Date().toISOString()
        };
        
        window.apiCalls.push(callInfo);
        
        try {
          const response = await originalFetch.apply(this, args);
          callInfo.status = response.status;
          callInfo.ok = response.ok;
          
          if (url.includes('/api/v1/travel/sessions')) {
            const cloned = response.clone();
            try {
              const data = await cloned.json();
              callInfo.responseData = data;
              console.log('[FETCH] Response:', data);
            } catch (e) {
              console.log('[FETCH] Could not parse response');
            }
          }
          
          return response;
        } catch (error) {
          callInfo.error = error.message;
          window.errors.push(error);
          console.error('[FETCH] Error:', error);
          throw error;
        }
      };
      
      // Monitor XMLHttpRequest as well
      const originalXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        const originalSend = xhr.send;
        
        xhr.open = function(method, url, ...args) {
          xhr._url = url;
          xhr._method = method;
          return originalOpen.apply(xhr, [method, url, ...args]);
        };
        
        xhr.send = function(body) {
          console.log('[XHR] Calling:', xhr._method, xhr._url);
          window.apiCalls.push({
            type: 'xhr',
            url: xhr._url,
            method: xhr._method,
            body: body,
            timestamp: new Date().toISOString()
          });
          return originalSend.apply(xhr, [body]);
        };
        
        return xhr;
      };
    `);
    
    console.log('📡 Network monitoring injected');
    
    // Clear logs
    await driver.manage().logs().get(logging.Type.BROWSER);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, I want to plan a trip');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for potential API call
    await driver.sleep(3000);
    
    // Get API calls
    const apiCalls = await driver.executeScript('return window.apiCalls || [];');
    const errors = await driver.executeScript('return window.errors || [];');
    
    console.log(`\n📡 API Calls Made: ${apiCalls.length}`);
    apiCalls.forEach((call, i) => {
      console.log(`\nCall ${i + 1}:`);
      console.log(`  URL: ${call.url}`);
      console.log(`  Method: ${call.method}`);
      console.log(`  Status: ${call.status}`);
      if (call.error) {
        console.log(`  ERROR: ${call.error}`);
      }
    });
    
    if (errors.length > 0) {
      console.log('\n❌ Errors:', errors);
    }
    
    // Get console logs
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Relevant Console Logs:');
    logs.forEach(entry => {
      const msg = entry.message;
      if (msg.includes('[useChatManager]') || msg.includes('[FETCH]') || msg.includes('[XHR]')) {
        console.log(msg);
      }
    });
    
    // Check messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Messages displayed: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 Last AI Response: "${lastMessage.substring(0, 100)}..."`);
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
apiCallTest().catch(console.error);