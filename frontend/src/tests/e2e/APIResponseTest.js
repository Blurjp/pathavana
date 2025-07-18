const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to check API response handling
 */
async function apiResponseTest() {
  console.log('🔍 API Response Test');
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
    
    // Inject detailed response monitoring
    await driver.executeScript(`
      window.apiResponses = [];
      
      // Override fetch to capture responses
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = args[0];
        console.log('[FETCH] Request to:', url);
        
        try {
          const response = await originalFetch.apply(this, args);
          const cloned = response.clone();
          
          // Try to parse as JSON
          try {
            const data = await cloned.json();
            console.log('[FETCH] Response data:', JSON.stringify(data, null, 2));
            
            window.apiResponses.push({
              url: url,
              status: response.status,
              ok: response.ok,
              data: data,
              timestamp: new Date().toISOString()
            });
          } catch (e) {
            console.log('[FETCH] Non-JSON response');
          }
          
          return response;
        } catch (error) {
          console.error('[FETCH] Error:', error);
          throw error;
        }
      };
      
      // Also override XMLHttpRequest
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
          console.log('[XHR] Request:', xhr._method, xhr._url, body);
          
          xhr.addEventListener('load', function() {
            try {
              const data = JSON.parse(xhr.responseText);
              console.log('[XHR] Response:', JSON.stringify(data, null, 2));
              
              window.apiResponses.push({
                url: xhr._url,
                status: xhr.status,
                ok: xhr.status >= 200 && xhr.status < 300,
                data: data,
                timestamp: new Date().toISOString(),
                type: 'xhr'
              });
            } catch (e) {
              console.log('[XHR] Non-JSON response');
            }
          });
          
          return originalSend.apply(xhr, [body]);
        };
        
        return xhr;
      };
    `);
    
    console.log('📡 Response monitoring injected');
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('I want to go to Paris');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get API responses
    const apiResponses = await driver.executeScript('return window.apiResponses || [];');
    
    console.log(`\n📡 API Responses Captured: ${apiResponses.length}`);
    apiResponses.forEach((resp, i) => {
      console.log(`\nResponse ${i + 1}:`);
      console.log(`  URL: ${resp.url}`);
      console.log(`  Status: ${resp.status}`);
      console.log(`  OK: ${resp.ok}`);
      console.log(`  Type: ${resp.type || 'fetch'}`);
      console.log(`  Data:`, JSON.stringify(resp.data, null, 2));
    });
    
    // Get console logs
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    console.log('\n📋 Console Errors:');
    logs.forEach(entry => {
      if (entry.level.name === 'SEVERE' || entry.message.includes('error')) {
        console.log(entry.message);
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
apiResponseTest().catch(console.error);