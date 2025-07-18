const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test dynamic quick prompts based on AI responses
 */
async function dynamicQuickPromptsTest() {
  console.log('🎯 Dynamic Quick Prompts Test');
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
    
    // Test 1: Check initial quick prompts
    console.log('\n📝 Test 1: Initial Quick Prompts');
    let quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${quickPrompts.length} initial quick prompts`);
    
    if (quickPrompts.length > 0) {
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        console.log(`  - Prompt ${i + 1}: "${text}"`);
      }
    }
    
    // Test 2: Send a message and check if prompts update
    console.log('\n📝 Test 2: Send Message and Check Updated Prompts');
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan a trip to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for AI response
    console.log('⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Get AI response
    const messages = await driver.findElements(By.css('.message-content'));
    if (messages.length >= 2) {
      const aiResponse = await messages[messages.length - 1].getText();
      console.log('\n🤖 AI Response:');
      console.log(aiResponse.substring(0, 200) + '...');
    }
    
    // Check if quick prompts updated
    await driver.sleep(2000);
    quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`\n✨ Found ${quickPrompts.length} updated quick prompts`);
    
    if (quickPrompts.length > 0) {
      console.log('Updated prompts:');
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        console.log(`  - Prompt ${i + 1}: "${text}"`);
        
        // Check if prompts are contextual to Tokyo
        if (text.toLowerCase().includes('tokyo') || 
            text.toLowerCase().includes('when') ||
            text.toLowerCase().includes('how long') ||
            text.toLowerCase().includes('budget')) {
          console.log('    ✅ Contextual prompt detected!');
        }
      }
    }
    
    // Test 3: Click a quick prompt
    console.log('\n📝 Test 3: Click Quick Prompt');
    if (quickPrompts.length > 0) {
      const firstPrompt = quickPrompts[0];
      const promptText = await firstPrompt.getText();
      console.log(`Clicking prompt: "${promptText}"`);
      
      await firstPrompt.click();
      await driver.sleep(2000);
      
      // Check if message was sent
      const newMessages = await driver.findElements(By.css('.message-content'));
      if (newMessages.length > messages.length) {
        console.log('✅ Quick prompt successfully sent a message!');
        const lastMessage = await newMessages[newMessages.length - 2].getText(); // -2 for user message
        console.log(`Sent message: "${lastMessage}"`);
      }
    }
    
    // Test 4: Check suggestions in AI response
    console.log('\n📝 Test 4: Check AI Response Suggestions');
    const suggestionButtons = await driver.findElements(By.css('.suggestion-buttons button'));
    console.log(`Found ${suggestionButtons.length} suggestion buttons in messages`);
    
    if (suggestionButtons.length > 0) {
      console.log('Suggestions in AI response:');
      for (let i = 0; i < Math.min(suggestionButtons.length, 3); i++) {
        const text = await suggestionButtons[i].getText();
        console.log(`  - Suggestion ${i + 1}: "${text}"`);
      }
    }
    
    console.log('\n✅ Dynamic Quick Prompts test completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Take screenshot on failure
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('dynamic-prompts-error.png', screenshot, 'base64');
    console.log('📸 Screenshot saved as dynamic-prompts-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
dynamicQuickPromptsTest().catch(console.error);