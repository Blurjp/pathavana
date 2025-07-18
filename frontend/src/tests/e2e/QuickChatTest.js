const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Quick test to check chat functionality
 */
async function quickChatTest() {
  console.log('🔍 Quick Chat Test');
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
    
    // Send a simple message
    await chatInput.sendKeys('Hi, I need help planning a trip');
    await chatInput.sendKeys(Key.RETURN);
    console.log('✅ Sent message');
    
    // Wait a bit and check page content
    await driver.sleep(5000);
    
    // Get all visible text on page
    const bodyText = await driver.findElement(By.tagName('body')).getText();
    console.log('\n📄 Page content preview:');
    console.log(bodyText.substring(0, 500) + '...');
    
    // Look for any error messages
    try {
      const errors = await driver.findElements(By.css('.error, .error-message, [class*="error"]'));
      if (errors.length > 0) {
        console.log('\n⚠️  Found error elements:');
        for (const error of errors) {
          const text = await error.getText();
          if (text) console.log(`   - ${text}`);
        }
      }
    } catch (e) {
      // No errors found
    }
    
    // Check console logs
    const logs = await driver.manage().logs().get('browser');
    const errors = logs.filter(entry => entry.level.name === 'SEVERE');
    if (errors.length > 0) {
      console.log('\n⚠️  Browser console errors:');
      errors.forEach(entry => console.log(`   - ${entry.message}`));
    }
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await driver.sleep(5000); // Keep open for inspection
    await driver.quit();
  }
}

quickChatTest().catch(console.error);