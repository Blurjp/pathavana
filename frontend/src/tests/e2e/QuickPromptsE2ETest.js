const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * E2E test for dynamic quick prompts functionality
 */
async function quickPromptsE2ETest() {
  console.log('🎯 Quick Prompts E2E Test');
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
    console.log('\n📝 Test 1: Checking initial quick prompts...');
    let quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    const initialPromptCount = quickPrompts.length;
    console.log(`Found ${initialPromptCount} initial quick prompts`);
    
    if (quickPrompts.length > 0) {
      const initialTexts = [];
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        initialTexts.push(text);
        console.log(`  Initial prompt ${i + 1}: "${text}"`);
      }
    }
    
    // Test 2: Send message and check console logs
    console.log('\n📝 Test 2: Sending message and monitoring console...');
    
    // Enable console log monitoring
    await driver.executeScript(`
      window.consoleLogs = [];
      const originalLog = console.log;
      console.log = function(...args) {
        window.consoleLogs.push(args.join(' '));
        originalLog.apply(console, args);
      };
    `);
    
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to plan a trip to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait for AI response
    console.log('⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    // Get console logs
    const consoleLogs = await driver.executeScript('return window.consoleLogs || []');
    console.log('\n📋 Console logs:');
    const relevantLogs = consoleLogs.filter(log => 
      log.includes('metadata') || 
      log.includes('UnifiedTravelRequest') ||
      log.includes('useChatManager') ||
      log.includes('suggestions')
    );
    
    relevantLogs.forEach(log => {
      console.log(`  > ${log}`);
    });
    
    // Test 3: Check if quick prompts changed
    console.log('\n📝 Test 3: Checking if quick prompts updated...');
    await driver.sleep(2000); // Give time for re-render
    
    quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${quickPrompts.length} quick prompts after AI response`);
    
    if (quickPrompts.length > 0) {
      const updatedTexts = [];
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        updatedTexts.push(text);
        console.log(`  Updated prompt ${i + 1}: "${text}"`);
      }
    }
    
    // Test 4: Check the AI message structure
    console.log('\n📝 Test 4: Checking AI message structure...');
    const messages = await driver.findElements(By.css('.message-content'));
    if (messages.length >= 2) {
      const aiMessage = messages[messages.length - 1];
      const aiText = await aiMessage.getText();
      console.log('AI Response preview:', aiText.substring(0, 100) + '...');
    }
    
    // Test 5: Manually check metadata
    console.log('\n📝 Test 5: Checking message metadata...');
    const messageData = await driver.executeScript(`
      // Try to access React component data
      const messages = document.querySelectorAll('[class*="message"]');
      const messageInfo = [];
      
      // Try to find React fiber
      for (const msg of messages) {
        const text = msg.textContent || '';
        messageInfo.push({
          text: text.substring(0, 50),
          className: msg.className
        });
      }
      
      return messageInfo;
    `);
    
    console.log('Message elements found:', messageData);
    
    // Test 6: Check if metadata is being passed correctly
    console.log('\n📝 Test 6: Debugging metadata flow...');
    const debugInfo = await driver.executeScript(`
      // Get the last console log about metadata
      const metadataLogs = (window.consoleLogs || []).filter(log => log.includes('metadata'));
      return {
        metadataLogCount: metadataLogs.length,
        lastMetadataLog: metadataLogs[metadataLogs.length - 1] || 'No metadata logs found',
        quickPromptCount: document.querySelectorAll('.quick-prompt').length,
        quickPromptTexts: Array.from(document.querySelectorAll('.quick-prompt')).map(el => el.textContent)
      };
    `);
    
    console.log('\n🔍 Debug Info:');
    console.log(`  Metadata log count: ${debugInfo.metadataLogCount}`);
    console.log(`  Last metadata log: ${debugInfo.lastMetadataLog}`);
    console.log(`  Quick prompt count: ${debugInfo.quickPromptCount}`);
    console.log(`  Quick prompt texts: ${JSON.stringify(debugInfo.quickPromptTexts, null, 2)}`);
    
    console.log('\n✅ Quick Prompts E2E test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Take screenshot on failure
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('quick-prompts-e2e-error.png', screenshot, 'base64');
    console.log('📸 Screenshot saved as quick-prompts-e2e-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
quickPromptsE2ETest().catch(console.error);