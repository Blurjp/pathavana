const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test AI message processing
 */
async function aiProcessingTest() {
  console.log('🤖 AI Processing Test');
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
    
    // Clear storage for fresh start
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
    
    // Find chat input
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      10000
    );
    console.log('✅ Found chat input');
    
    // Test 1: Send a specific travel request
    console.log('\n📝 Test 1: Specific travel request');
    await chatInput.clear();
    await chatInput.sendKeys('Find me flights from San Francisco to Tokyo for December 15-22');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for AI response
    await driver.sleep(6000);
    
    let messages = await driver.findElements(By.css('.message-content'));
    console.log(`Messages after test 1: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log('\nAI Response:');
      console.log(lastMessage);
      
      // Check if response is contextual
      const isContextual = 
        lastMessage.includes('Tokyo') || 
        lastMessage.includes('San Francisco') || 
        lastMessage.includes('December') ||
        lastMessage.includes('flight') ||
        lastMessage.includes('search');
      
      if (isContextual) {
        console.log('✅ AI response is contextual!');
      } else {
        console.log('❌ AI response is generic');
      }
    }
    
    // Test 2: Follow-up message
    console.log('\n📝 Test 2: Follow-up message');
    await chatInput.clear();
    await chatInput.sendKeys('I prefer direct flights only');
    await chatInput.sendKeys(Key.RETURN);
    
    await driver.sleep(5000);
    
    messages = await driver.findElements(By.css('.message-content'));
    if (messages.length >= 4) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log('\nAI Follow-up Response:');
      console.log(lastMessage.substring(0, 200) + '...');
    }
    
    // Check console logs for search activity
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    const searchLogs = logs.filter(entry => 
      entry.message.includes('Search triggered') || 
      entry.message.includes('search')
    );
    
    console.log(`\n🔍 Search activity logs: ${searchLogs.length}`);
    
    console.log('\n🎉 Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
aiProcessingTest().catch(console.error);