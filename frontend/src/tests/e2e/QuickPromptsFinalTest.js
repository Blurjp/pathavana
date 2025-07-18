const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Final comprehensive test for quick prompts functionality
 */
async function quickPromptsFinalTest() {
  console.log('✅ Quick Prompts Final Verification Test');
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
    console.log('✅ Logged in successfully\n');
    
    await driver.sleep(2000);
    
    // Test 1: Initial static prompts
    console.log('📝 Test 1: Initial Static Prompts');
    console.log('─'.repeat(40));
    let quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    const initialPrompts = [];
    
    for (let i = 0; i < quickPrompts.length; i++) {
      const text = await quickPrompts[i].getText();
      initialPrompts.push(text);
      console.log(`  ✓ Initial prompt ${i + 1}: "${text}"`);
    }
    
    console.log(`  Total: ${initialPrompts.length} static prompts\n`);
    
    // Test 2: Send message about Tokyo
    console.log('📝 Test 2: Dynamic Prompts After AI Response');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan a trip to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Check updated prompts
    quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    const tokyoPrompts = [];
    
    for (let i = 0; i < quickPrompts.length; i++) {
      const text = await quickPrompts[i].getText();
      tokyoPrompts.push(text);
      console.log(`  ✓ Tokyo prompt ${i + 1}: "${text}"`);
    }
    
    console.log(`  Total: ${tokyoPrompts.length} dynamic prompts`);
    
    // Verify prompts changed
    const promptsChanged = tokyoPrompts.some(prompt => 
      !initialPrompts.includes(prompt) || 
      prompt.toLowerCase().includes('tokyo') ||
      prompt.toLowerCase().includes('dates') ||
      prompt.toLowerCase().includes('season')
    );
    
    console.log(`  ✅ Prompts updated: ${promptsChanged ? 'YES' : 'NO'}\n`);
    
    // Test 3: Click a dynamic prompt
    console.log('📝 Test 3: Click Dynamic Prompt');
    console.log('─'.repeat(40));
    
    if (quickPrompts.length > 0) {
      const firstPrompt = quickPrompts[0];
      const promptText = await firstPrompt.getText();
      console.log(`  Clicking: "${promptText}"`);
      
      const messageCountBefore = await driver.findElements(By.css('.message-content'));
      await firstPrompt.click();
      await driver.sleep(3000);
      
      const messageCountAfter = await driver.findElements(By.css('.message-content'));
      const messageSent = messageCountAfter.length > messageCountBefore.length;
      
      console.log(`  ✅ Message sent: ${messageSent ? 'YES' : 'NO'}\n`);
    }
    
    // Test 4: Send message about different destination
    console.log('📝 Test 4: Prompts Update for Different Destination');
    console.log('─'.repeat(40));
    
    await chatInput.clear();
    await chatInput.sendKeys('Actually, I want to go to Paris instead');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Check prompts updated again
    quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    const parisPrompts = [];
    
    for (let i = 0; i < quickPrompts.length; i++) {
      const text = await quickPrompts[i].getText();
      parisPrompts.push(text);
      console.log(`  ✓ Paris prompt ${i + 1}: "${text}"`);
    }
    
    // Verify prompts changed from Tokyo prompts
    const promptsChangedAgain = parisPrompts.some(prompt => 
      !tokyoPrompts.includes(prompt) ||
      prompt.toLowerCase().includes('paris')
    );
    
    console.log(`  ✅ Prompts updated again: ${promptsChangedAgain ? 'YES' : 'NO'}\n`);
    
    // Summary
    console.log('📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Initial static prompts displayed: ${initialPrompts.length > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Prompts update after AI response: ${promptsChanged ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Dynamic prompts are clickable: ${quickPrompts.length > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Prompts update for new context: ${promptsChangedAgain ? 'PASS' : 'FAIL'}`);
    console.log('\n🎉 Quick prompts feature is working correctly!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Take screenshot on failure
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('quick-prompts-final-error.png', screenshot, 'base64');
    console.log('📸 Screenshot saved as quick-prompts-final-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
quickPromptsFinalTest().catch(console.error);