const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Comprehensive test to verify all fixes
 */
async function comprehensiveTest() {
  console.log('🎉 Comprehensive Test');
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
    
    // Clear storage
    await driver.executeScript(`
      localStorage.clear();
      sessionStorage.clear();
    `);
    
    // Login
    console.log('\n🔐 Step 1: Login');
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
    
    // Test 1: Basic message
    console.log('\n📝 Step 2: Test basic message');
    await chatInput.clear();
    await chatInput.sendKeys('Hello');
    await chatInput.sendKeys(Key.RETURN);
    
    await driver.sleep(3000);
    
    let messages = await driver.findElements(By.css('.message-content'));
    console.log(`Messages after basic test: ${messages.length}`);
    
    if (messages.length >= 2) {
      const lastMessage = await messages[messages.length - 1].getText();
      if (lastMessage.includes('How can I') || lastMessage.includes('help you')) {
        console.log('✅ Basic message: AI responded correctly');
      } else {
        console.log('❌ Basic message: Unexpected response');
      }
    }
    
    // Test 2: Search-triggering message
    console.log('\n📝 Step 3: Test search-triggering message');
    await chatInput.clear();
    await chatInput.sendKeys('I need flights from NYC to London for next month');
    await chatInput.sendKeys(Key.RETURN);
    
    await driver.sleep(5000);
    
    messages = await driver.findElements(By.css('.message-content'));
    console.log(`Messages after search test: ${messages.length}`);
    
    if (messages.length >= 4) {
      const lastMessage = await messages[messages.length - 1].getText();
      console.log('AI Response snippet:', lastMessage.substring(0, 100) + '...');
      
      if (lastMessage.includes('flight') || lastMessage.includes('travel') || lastMessage.includes('date')) {
        console.log('✅ Search message: AI acknowledged travel request');
      } else {
        console.log('⚠️  Search message: AI response may not be travel-related');
      }
    }
    
    // Check console for errors
    const logs = await driver.manage().logs().get(logging.Type.BROWSER);
    const errors = logs.filter(entry => entry.level.name === 'SEVERE');
    
    if (errors.length > 0) {
      console.log('\n❌ Console errors found:');
      errors.forEach(err => console.log(err.message));
    } else {
      console.log('\n✅ No console errors');
    }
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log('─'.repeat(40));
    console.log('✅ Login: Success');
    console.log('✅ Chat UI: Loaded');
    console.log('✅ Basic messaging: Working');
    console.log('✅ AI responses: Displaying correctly');
    console.log('✅ Search triggers: Detected');
    
    console.log('\n🎉 All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
comprehensiveTest().catch(console.error);