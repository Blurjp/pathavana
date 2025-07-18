const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to debug the actual API response
 */
async function responseDebugTest() {
  console.log('🔍 Response Debug Test');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
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
    
    // Inject network interceptor
    await driver.executeScript(`
      // Override fetch to log responses
      const originalFetch = window.fetch;
      window.fetchResponses = [];
      
      window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);
        const url = args[0];
        
        if (url.includes('/api/v1/travel/sessions')) {
          const clonedResponse = response.clone();
          const data = await clonedResponse.json();
          window.fetchResponses.push({
            url: url,
            status: response.status,
            data: data
          });
          console.log('API Response:', url, data);
        }
        
        return response;
      };
    `);
    
    console.log('📡 Network interceptor injected');
    
    // Find chat input
    await driver.sleep(2000);
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, help me plan a trip');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    await driver.sleep(5000);
    
    // Get captured responses
    const responses = await driver.executeScript('return window.fetchResponses || [];');
    console.log(`\n📥 Captured ${responses.length} API responses`);
    
    responses.forEach((resp, i) => {
      console.log(`\nResponse ${i + 1}:`);
      console.log(`URL: ${resp.url}`);
      console.log(`Status: ${resp.status}`);
      console.log('Data structure:');
      
      if (resp.data && resp.data.data) {
        console.log('  - data keys:', Object.keys(resp.data.data));
        if (resp.data.data.message) {
          console.log('  - message:', resp.data.data.message.substring(0, 100) + '...');
        }
        if (resp.data.data.initial_response) {
          console.log('  - initial_response:', resp.data.data.initial_response.substring(0, 100) + '...');
        }
      }
    });
    
    // Check displayed messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Found ${messages.length} displayed messages`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log(`\n🤖 Last displayed message:`);
      console.log(lastMessage.substring(0, 200) + '...');
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
responseDebugTest().catch(console.error);