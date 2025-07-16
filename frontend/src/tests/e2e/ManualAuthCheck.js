const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Manual authentication check - keeps browser open for inspection
 */
async function manualAuthCheck() {
  console.log('🔍 Manual Authentication Check');
  console.log('This will keep the browser open for manual inspection');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  try {
    // Navigate to homepage
    await driver.get('http://localhost:3000');
    console.log('✅ Opened homepage');
    
    // Wait for page load
    await driver.sleep(2000);
    
    // Click Sign In
    const signInButton = await driver.findElement(By.css('.auth-buttons button:first-child'));
    await signInButton.click();
    console.log('✅ Clicked Sign In');
    
    await driver.sleep(1000);
    
    // Fill form
    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    await emailInput.clear();
    await emailInput.sendKeys('selenium.test@example.com');
    console.log('✅ Entered email: selenium.test@example.com');
    
    const passwordInput = await driver.findElement(By.css('input[type="password"]'));
    await passwordInput.clear();
    await passwordInput.sendKeys('SeleniumTest123!');
    console.log('✅ Entered password: SeleniumTest123!');
    
    console.log('\n📋 Next Steps:');
    console.log('1. Check if the form looks correct');
    console.log('2. Click the Sign In button manually');
    console.log('3. Watch for any error messages');
    console.log('4. Check browser console for errors (F12)');
    console.log('5. Check Network tab for failed requests');
    
    console.log('\n⏸️  Browser will stay open for 60 seconds...');
    console.log('Press Ctrl+C to close earlier');
    
    // Keep browser open for inspection
    await driver.sleep(60000);
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await driver.quit();
    console.log('\n✅ Browser closed');
  }
}

manualAuthCheck().catch(console.error);