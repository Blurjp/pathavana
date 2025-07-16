const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

/**
 * Debug Authentication Test
 * Step-by-step test to diagnose authentication issues
 */
class DebugAuthTest {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000';
    this.testUser = {
      email: 'selenium.test@example.com',
      password: 'SeleniumTest123!'
    };
  }

  async run() {
    console.log('🔍 Debug Authentication Test');
    console.log('═'.repeat(60));
    console.log(`📧 Test Email: ${this.testUser.email}`);
    console.log(`🔑 Test Password: ${this.testUser.password}`);
    console.log('═'.repeat(60));
    
    try {
      // Setup
      const options = new chrome.Options();
      options.addArguments('--window-size=1920,1080');
      options.addArguments('--disable-dev-shm-usage');
      options.addArguments('--no-sandbox');
      
      this.driver = await new Builder()
        .forBrowser('chrome')
        .setChromeOptions(options)
        .build();
      
      console.log('\n✅ Chrome started');
      
      // Step 1: Navigate to homepage
      console.log('\n📍 Step 1: Navigate to Homepage');
      console.log('━'.repeat(50));
      await this.driver.get(this.baseUrl);
      await this.driver.sleep(3000);
      
      const url = await this.driver.getCurrentUrl();
      const title = await this.driver.getTitle();
      console.log(`   URL: ${url}`);
      console.log(`   Title: ${title}`);
      
      await this.screenshot('01-homepage');
      
      // Step 2: Check current auth state
      console.log('\n🔐 Step 2: Check Authentication State');
      console.log('━'.repeat(50));
      
      // Check for user avatar (logged in)
      try {
        const avatar = await this.driver.findElement(By.css('.user-avatar, .avatar-placeholder'));
        console.log('   ✅ User appears to be logged in already');
        
        // Get user info if visible
        try {
          await avatar.click();
          await this.driver.sleep(1000);
          const userInfo = await this.driver.findElement(By.css('.user-info, .user-menu-dropdown'));
          const infoText = await userInfo.getText();
          console.log(`   User info: ${infoText}`);
        } catch (e) {
          console.log('   Could not get user info');
        }
        
        await this.screenshot('02-already-logged-in');
        return;
      } catch (e) {
        console.log('   ℹ️  Not logged in - proceeding with login');
      }
      
      // Step 3: Find Sign In button
      console.log('\n🔍 Step 3: Find Sign In Button');
      console.log('━'.repeat(50));
      
      // Try multiple ways to find sign in button
      const signInSelectors = [
        '.auth-buttons button:first-child',
        '.auth-buttons button',
        'button.btn-secondary',
        'button',
        '.header button'
      ];
      
      let signInButton = null;
      for (const selector of signInSelectors) {
        try {
          const buttons = await this.driver.findElements(By.css(selector));
          console.log(`   Found ${buttons.length} elements matching: ${selector}`);
          
          for (const button of buttons) {
            const text = await button.getText();
            const isDisplayed = await button.isDisplayed();
            console.log(`     Button text: "${text}", displayed: ${isDisplayed}`);
            
            if (text.toLowerCase().includes('sign in') && isDisplayed) {
              signInButton = button;
              console.log('   ✅ Found Sign In button!');
              break;
            }
          }
          
          if (signInButton) break;
        } catch (e) {
          console.log(`   Error with selector ${selector}: ${e.message}`);
        }
      }
      
      if (!signInButton) {
        console.log('\n   ❌ Could not find Sign In button');
        console.log('   📋 Page source sample:');
        const pageSource = await this.driver.getPageSource();
        const headerMatch = pageSource.match(/<header[^>]*>[\s\S]*?<\/header>/i);
        if (headerMatch) {
          console.log(headerMatch[0].substring(0, 500) + '...');
        }
        await this.screenshot('03-no-signin-button');
        return;
      }
      
      // Step 4: Click Sign In
      console.log('\n👆 Step 4: Click Sign In Button');
      console.log('━'.repeat(50));
      await signInButton.click();
      console.log('   ✅ Clicked Sign In button');
      await this.driver.sleep(2000);
      
      await this.screenshot('04-after-signin-click');
      
      // Step 5: Find login form
      console.log('\n📝 Step 5: Find Login Form');
      console.log('━'.repeat(50));
      
      // Look for email input
      const emailSelectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="email" i]',
        'input[id*="email" i]',
        '.login-modal input',
        '.modal input'
      ];
      
      let emailInput = null;
      for (const selector of emailSelectors) {
        try {
          const inputs = await this.driver.findElements(By.css(selector));
          console.log(`   Found ${inputs.length} inputs matching: ${selector}`);
          
          for (const input of inputs) {
            if (await input.isDisplayed()) {
              emailInput = input;
              console.log('   ✅ Found email input');
              break;
            }
          }
          
          if (emailInput) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!emailInput) {
        console.log('   ❌ Could not find email input');
        await this.screenshot('05-no-email-input');
        return;
      }
      
      // Step 6: Fill login form
      console.log('\n✍️  Step 6: Fill Login Form');
      console.log('━'.repeat(50));
      
      // Enter email
      await emailInput.clear();
      await emailInput.sendKeys(this.testUser.email);
      console.log(`   ✅ Entered email: ${this.testUser.email}`);
      
      // Find password input
      const passwordInput = await this.driver.findElement(By.css('input[type="password"]'));
      await passwordInput.clear();
      await passwordInput.sendKeys(this.testUser.password);
      console.log(`   ✅ Entered password: ${'*'.repeat(this.testUser.password.length)}`);
      
      await this.screenshot('06-form-filled');
      
      // Step 7: Submit form
      console.log('\n📤 Step 7: Submit Login Form');
      console.log('━'.repeat(50));
      
      // Try multiple ways to submit
      let submitted = false;
      
      // Method 1: Look for submit button
      try {
        const submitButtons = await this.driver.findElements(By.css('button'));
        for (const button of submitButtons) {
          const text = await button.getText();
          if (text.toLowerCase().includes('sign in') || 
              text.toLowerCase().includes('login') ||
              text.toLowerCase().includes('submit')) {
            await button.click();
            console.log(`   ✅ Clicked submit button: "${text}"`);
            submitted = true;
            break;
          }
        }
      } catch (e) {
        console.log('   Could not find submit button');
      }
      
      // Method 2: Press Enter
      if (!submitted) {
        await passwordInput.sendKeys(Key.RETURN);
        console.log('   ✅ Submitted with Enter key');
      }
      
      // Step 8: Wait for result
      console.log('\n⏳ Step 8: Wait for Authentication Result');
      console.log('━'.repeat(50));
      
      // Wait a bit for processing
      await this.driver.sleep(3000);
      
      // Check for error messages
      try {
        const errorElements = await this.driver.findElements(By.css('.error, .alert, [class*="error"]'));
        for (const elem of errorElements) {
          const text = await elem.getText();
          if (text) {
            console.log(`   ⚠️  Error message: "${text}"`);
          }
        }
      } catch (e) {
        // No errors found
      }
      
      // Check if logged in
      try {
        await this.driver.wait(until.elementLocated(By.css('.user-avatar, .avatar-placeholder')), 5000);
        console.log('   ✅ Login successful! User avatar found');
        await this.screenshot('07-login-success');
      } catch (e) {
        console.log('   ❌ Login failed - no user avatar found');
        await this.screenshot('07-login-failed');
        
        // Check current URL
        const currentUrl = await this.driver.getCurrentUrl();
        console.log(`   Current URL: ${currentUrl}`);
      }
      
    } catch (error) {
      console.error('\n❌ Test error:', error.message);
      await this.screenshot('error');
    } finally {
      console.log('\n🧹 Cleaning up...');
      if (this.driver) {
        await this.driver.quit();
      }
    }
  }

  async screenshot(name) {
    try {
      const dir = path.join(__dirname, 'screenshots', 'debug-auth');
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      const screenshot = await this.driver.takeScreenshot();
      const filename = path.join(dir, `${name}-${Date.now()}.png`);
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`   📸 Screenshot: ${filename}`);
    } catch (e) {
      console.error(`   Screenshot failed: ${e.message}`);
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new DebugAuthTest();
  test.run().catch(console.error);
}

module.exports = DebugAuthTest;