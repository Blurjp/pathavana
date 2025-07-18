const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to check session handling
 */
async function sessionDebugTest() {
  console.log('🔍 Session Debug Test');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  try {
    // Navigate
    await driver.get('http://localhost:3000');
    await driver.sleep(2000);
    
    // Clear all storage before login
    await driver.executeScript(`
      localStorage.clear();
      sessionStorage.clear();
      console.log('Storage cleared');
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
    
    // Check initial storage
    await driver.sleep(2000);
    const initialStorage = await driver.executeScript(`
      return {
        localStorage: Object.keys(localStorage).filter(k => k.includes('pathavana')),
        sessionStorage: Object.keys(sessionStorage).filter(k => k.includes('pathavana')),
        sessionId: localStorage.getItem('pathavana_session_id')
      };
    `);
    console.log('\n📦 Initial Storage:', initialStorage);
    
    // Add extensive logging
    await driver.executeScript(`
      // Log all relevant function calls
      window.debugInfo = {
        apiCalls: [],
        sessionUpdates: [],
        messages: []
      };
      
      // Override fetch to log API calls
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = args[0];
        const options = args[1] || {};
        
        window.debugInfo.apiCalls.push({
          url: url,
          method: options.method || 'GET',
          body: options.body ? JSON.parse(options.body) : null
        });
        
        const response = await originalFetch.apply(this, args);
        
        if (url.includes('/api/v1/travel/sessions')) {
          const clonedResponse = response.clone();
          const data = await clonedResponse.json();
          
          window.debugInfo.apiCalls[window.debugInfo.apiCalls.length - 1].response = data;
          
          // Check for session creation
          if (data.data && data.data.session_id && !url.includes('chat')) {
            window.debugInfo.sessionUpdates.push({
              type: 'created',
              sessionId: data.data.session_id
            });
          }
        }
        
        return response;
      };
      
      // Override localStorage.setItem to track session updates
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = function(key, value) {
        if (key.includes('session')) {
          window.debugInfo.sessionUpdates.push({
            type: 'localStorage',
            key: key,
            value: value
          });
        }
        return originalSetItem.apply(this, arguments);
      };
    `);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('\n✅ Found chat input');
    
    // Send a message
    console.log('📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, help me plan a trip to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get debug info
    const debugInfo = await driver.executeScript('return window.debugInfo;');
    
    console.log('\n📡 API Calls:', debugInfo.apiCalls.length);
    debugInfo.apiCalls.forEach((call, i) => {
      console.log(`\nCall ${i + 1}:`);
      console.log(`  URL: ${call.url}`);
      console.log(`  Method: ${call.method}`);
      if (call.body) {
        console.log(`  Body:`, call.body);
      }
      if (call.response && call.response.data) {
        console.log(`  Response has session_id:`, !!call.response.data.session_id);
        console.log(`  Response has message:`, !!call.response.data.message);
        console.log(`  Response has initial_response:`, !!call.response.data.initial_response);
      }
    });
    
    console.log('\n🔑 Session Updates:', debugInfo.sessionUpdates);
    
    // Check final storage
    const finalStorage = await driver.executeScript(`
      return {
        sessionId: localStorage.getItem('pathavana_session_id'),
        messages: JSON.parse(localStorage.getItem('pathavana_messages_' + localStorage.getItem('pathavana_session_id')) || '[]').length
      };
    `);
    console.log('\n📦 Final Storage:', finalStorage);
    
    // Check displayed messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Displayed ${messages.length} messages`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 Last AI Response:`);
      console.log(lastMessage.substring(0, 100) + '...');
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
sessionDebugTest().catch(console.error);