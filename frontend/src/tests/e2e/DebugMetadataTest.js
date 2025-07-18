const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to check AI response metadata
 */
async function debugMetadataTest() {
  console.log('🔍 Debug Metadata Test');
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
    
    // Send a message
    console.log('\n📝 Sending message...');
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan a trip to Tokyo next month');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for AI response
    console.log('⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Get console logs to see metadata
    console.log('\n📋 Browser Console Logs:');
    const logs = await driver.manage().logs().get('browser');
    
    const relevantLogs = logs.filter(entry => 
      entry.message.includes('useChatManager') || 
      entry.message.includes('UnifiedTravelRequest') ||
      entry.message.includes('metadata')
    );
    
    for (const log of relevantLogs) {
      console.log(`[${log.level.name}] ${log.message}`);
    }
    
    // Check API response directly
    console.log('\n🔍 Checking API response data...');
    const apiData = await driver.executeScript(`
      // Try to capture the last API response from network
      return window.lastApiResponse || 'No API response captured';
    `);
    console.log('API Data:', apiData);
    
    console.log('\n✅ Debug test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
debugMetadataTest().catch(console.error);