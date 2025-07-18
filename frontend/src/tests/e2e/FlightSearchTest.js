const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test specific flight search
 */
async function flightSearchTest() {
  console.log('✈️  Flight Search Test');
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
    
    // Send explicit search request
    console.log('\n📝 Sending explicit flight search request...');
    await chatInput.clear();
    await chatInput.sendKeys('Search for flights from Los Angeles LAX to Tokyo NRT on December 20, 2024');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait longer for search
    console.log('\n⏳ Waiting for AI to process and search...');
    await driver.sleep(8000);
    
    // Get messages
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Messages displayed: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log('\n🤖 AI Response:');
      console.log(lastMessage);
      
      // Check if response mentions search or flights
      const isSearching = 
        lastMessage.includes('search') || 
        lastMessage.includes('looking') || 
        lastMessage.includes('LAX') ||
        lastMessage.includes('Tokyo') ||
        lastMessage.includes('December 20') ||
        lastMessage.includes('flight');
      
      if (isSearching) {
        console.log('\n✅ AI acknowledged flight search request!');
      } else {
        console.log('\n⚠️  AI did not acknowledge search request');
      }
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
flightSearchTest().catch(console.error);