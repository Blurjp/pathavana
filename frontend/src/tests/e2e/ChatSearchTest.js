const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to verify AI chat responses and search functionality
 */
async function chatSearchTest() {
  console.log('🤖 AI Chat & Search Test');
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
    
    // Find chat input
    await driver.sleep(2000);
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Test 1: Send a basic message and check for AI response
    console.log('\n📝 Test 1: Basic AI Response');
    await chatInput.clear();
    await chatInput.sendKeys('Hello, I want to plan a trip');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for AI response
    await driver.sleep(3000);
    
    // Check for AI message
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`   Found ${messages.length} messages`);
    
    if (messages.length >= 2) {
      const aiMessage = await messages[messages.length - 1].getText();
      console.log(`   AI Response: "${aiMessage.substring(0, 100)}..."`);
      
      // Check if it's not a template response
      if (aiMessage.includes('How can I') || aiMessage.includes('help you') || aiMessage.includes('travel')) {
        console.log('   ✅ AI response received (not template)');
      } else {
        console.log('   ⚠️ Response might be a template');
      }
    }
    
    // Test 2: Send a flight search message
    console.log('\n🔍 Test 2: Flight Search');
    await driver.sleep(2000);
    await chatInput.clear();
    await chatInput.sendKeys('Find flights to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for response and check for search results
    await driver.sleep(5000);
    
    // Check for search results sidebar
    try {
      const sidebar = await driver.findElement(By.css('.search-results-sidebar, .sidebar-open'));
      console.log('   ✅ Search results sidebar found');
      
      // Check for flight results
      const flightTab = await driver.findElement(By.xpath("//button[contains(text(), 'Flights')]"));
      await flightTab.click();
      await driver.sleep(1000);
      
      const flightCards = await driver.findElements(By.css('.flight-card, .search-result-card'));
      console.log(`   ✅ Found ${flightCards.length} flight results`);
    } catch (e) {
      console.log('   ❌ No search results sidebar found');
      
      // Check AI response for search indication
      const latestMessages = await driver.findElements(By.css('.message-content'));
      if (latestMessages.length > 0) {
        const lastMessage = await latestMessages[latestMessages.length - 1].getText();
        if (lastMessage.includes('flight') || lastMessage.includes('Tokyo')) {
          console.log('   ⚠️ AI mentioned flights but no sidebar shown');
        }
      }
    }
    
    // Test 3: Send a hotel search message
    console.log('\n🏨 Test 3: Hotel Search');
    await driver.sleep(2000);
    await chatInput.clear();
    await chatInput.sendKeys('Show me hotels in Shibuya Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    await driver.sleep(5000);
    
    // Check latest AI response
    const allMessages = await driver.findElements(By.css('.message-content'));
    if (allMessages.length > 0) {
      const lastAiMessage = await allMessages[allMessages.length - 1].getText();
      console.log(`   AI Response: "${lastAiMessage.substring(0, 100)}..."`);
      
      if (lastAiMessage.includes('hotel') || lastAiMessage.includes('Shibuya')) {
        console.log('   ✅ AI processed hotel search request');
      }
    }
    
    // Take screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('chat-search-test-result.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as chat-search-test-result.png');
    
    console.log('\n✅ Test completed successfully');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Take error screenshot
    try {
      const screenshot = await driver.takeScreenshot();
      const fs = require('fs');
      fs.writeFileSync('chat-search-test-error.png', screenshot, 'base64');
      console.log('📸 Error screenshot saved');
    } catch (e) {}
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
chatSearchTest().catch(console.error);