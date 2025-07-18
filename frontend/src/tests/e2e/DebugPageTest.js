const { Builder, By, until, Key, logging } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to debug page content
 */
async function debugPageTest() {
  console.log('🔍 Debug Page Test');
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
    
    await driver.sleep(3000);
    
    // Debug page content
    console.log('\n🔍 Page Analysis:');
    console.log('─'.repeat(40));
    
    // Get current URL
    const currentUrl = await driver.getCurrentUrl();
    console.log('Current URL:', currentUrl);
    
    // Get page title
    const pageTitle = await driver.getTitle();
    console.log('Page Title:', pageTitle);
    
    // Get all textareas
    const textareas = await driver.findElements(By.css('textarea'));
    console.log(`\nTextareas found: ${textareas.length}`);
    
    for (let i = 0; i < textareas.length; i++) {
      const placeholder = await textareas[i].getAttribute('placeholder');
      const isVisible = await textareas[i].isDisplayed();
      console.log(`  Textarea ${i + 1}: placeholder="${placeholder}", visible=${isVisible}`);
    }
    
    // Get all inputs
    const inputs = await driver.findElements(By.css('input[type="text"], input[type="search"]'));
    console.log(`\nText inputs found: ${inputs.length}`);
    
    for (let i = 0; i < inputs.length; i++) {
      const placeholder = await inputs[i].getAttribute('placeholder');
      const isVisible = await inputs[i].isDisplayed();
      console.log(`  Input ${i + 1}: placeholder="${placeholder}", visible=${isVisible}`);
    }
    
    // Get page body text snippet
    const bodyText = await driver.findElement(By.tagName('body')).getText();
    console.log('\nPage text snippet:', bodyText.substring(0, 200) + '...');
    
    // Try to find chat-related elements
    console.log('\n📋 Looking for chat elements:');
    
    try {
      const chatContainer = await driver.findElement(By.css('.chat-container, [class*="chat"]'));
      console.log('✅ Found chat container');
    } catch (e) {
      console.log('❌ No chat container found');
    }
    
    try {
      const messageArea = await driver.findElement(By.css('[class*="message"]'));
      console.log('✅ Found message area');
    } catch (e) {
      console.log('❌ No message area found');
    }
    
    console.log('\n✅ Debug completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
debugPageTest().catch(console.error);