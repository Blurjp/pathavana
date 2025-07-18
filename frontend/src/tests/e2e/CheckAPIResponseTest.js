const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to check what the API is actually returning
 */
async function checkAPIResponseTest() {
  console.log('🔍 Check API Response Test');
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
    
    // Wait for chat page
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully');
    
    await driver.sleep(2000);
    
    // Enable console log capture
    await driver.executeScript(`
      window.apiLogs = [];
      const originalLog = console.log;
      console.log = function(...args) {
        if (args[0] && typeof args[0] === 'string' && args[0].includes('Full response.data:')) {
          window.apiLogs.push(args.join(' '));
        }
        originalLog.apply(console, args);
      };
    `);
    
    // Send a message
    console.log('\n📝 Sending message...');
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan a trip to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response
    console.log('⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Get the captured API logs
    const apiLogs = await driver.executeScript('return window.apiLogs || []');
    
    console.log('\n📋 API Response Data:');
    console.log('═'.repeat(60));
    
    if (apiLogs.length > 0) {
      // Extract the JSON from the log
      const fullLog = apiLogs[0];
      const jsonStart = fullLog.indexOf('{');
      if (jsonStart !== -1) {
        const jsonData = fullLog.substring(jsonStart);
        try {
          const parsed = JSON.parse(jsonData);
          console.log(JSON.stringify(parsed, null, 2));
        } catch (e) {
          console.log('Raw log:', fullLog);
        }
      }
    } else {
      console.log('No API response logs captured');
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
checkAPIResponseTest().catch(console.error);