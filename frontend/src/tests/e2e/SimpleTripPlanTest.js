const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

/**
 * Simplified Trip Plan Test - More robust version
 */
class SimpleTripPlanTest {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000';
  }

  async run() {
    try {
      // Setup Chrome
      console.log('🚀 Starting Simple Trip Plan Test');
      console.log('━'.repeat(50));
      
      const options = new chrome.Options();
      options.addArguments('--window-size=1920,1080');
      options.addArguments('--disable-dev-shm-usage');
      options.addArguments('--no-sandbox');
      
      this.driver = await new Builder()
        .forBrowser('chrome')
        .setChromeOptions(options)
        .build();
      
      console.log('✅ Chrome started');
      
      // Step 1: Navigate to homepage
      console.log('\n📍 Step 1: Navigate to Homepage');
      console.log('━'.repeat(50));
      
      console.log(`   Going to: ${this.baseUrl}`);
      await this.driver.get(this.baseUrl);
      
      // Wait a bit and check where we are
      await this.driver.sleep(3000);
      
      const currentUrl = await this.driver.getCurrentUrl();
      const title = await this.driver.getTitle();
      
      console.log(`   Current URL: ${currentUrl}`);
      console.log(`   Page Title: ${title}`);
      
      // Take screenshot
      await this.takeScreenshot('01-homepage');
      
      // Step 2: Check for Sign In button
      console.log('\n🔐 Step 2: Authentication Check');
      console.log('━'.repeat(50));
      
      try {
        // Look for user avatar (already logged in)
        const avatar = await this.driver.findElement(By.css('.user-avatar, .avatar-placeholder'));
        console.log('   ✅ User is already logged in');
        await this.takeScreenshot('02-logged-in');
      } catch (e) {
        // Not logged in, look for sign in button
        console.log('   ⚠️  User not logged in');
        
        try {
          const signInBtn = await this.driver.findElement(By.css('.auth-buttons button'));
          console.log('   ✅ Found Sign In button');
          await this.takeScreenshot('02-not-logged-in');
          
          // For this test, we'll stop here and show instructions
          console.log('\n   📝 Manual Login Required:');
          console.log('   1. Click the Sign In button');
          console.log('   2. Enter test credentials:');
          console.log('      Email: test@example.com');
          console.log('      Password: testpassword');
          console.log('   3. Run the test again after logging in');
          
          return;
        } catch (e2) {
          console.log('   ❌ Could not find Sign In button');
          await this.takeScreenshot('02-no-auth-buttons');
        }
      }
      
      // Step 3: Navigate to Chat
      console.log('\n💬 Step 3: Navigate to Chat');
      console.log('━'.repeat(50));
      
      // Check if we're already on chat page
      if (currentUrl.includes('/chat')) {
        console.log('   ✅ Already on chat page');
      } else {
        // Try to find and click Chat link
        try {
          const chatLink = await this.driver.findElement(By.css('a[href="/chat"]'));
          await chatLink.click();
          console.log('   ✅ Clicked Chat link');
          
          await this.driver.sleep(2000);
          const newUrl = await this.driver.getCurrentUrl();
          console.log(`   New URL: ${newUrl}`);
        } catch (e) {
          // Navigate directly
          console.log('   📍 Navigating directly to /chat');
          await this.driver.get(`${this.baseUrl}/chat`);
          await this.driver.sleep(2000);
        }
      }
      
      await this.takeScreenshot('03-chat-page');
      
      // Step 4: Find Chat Input
      console.log('\n🔍 Step 4: Find Chat Input');
      console.log('━'.repeat(50));
      
      let chatInput = null;
      const selectors = [
        'textarea',
        'input[type="text"]',
        '.chat-input textarea',
        '.chat-input input'
      ];
      
      for (const selector of selectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          console.log(`   Found ${elements.length} ${selector} elements`);
          
          for (const element of elements) {
            const isDisplayed = await element.isDisplayed();
            const placeholder = await element.getAttribute('placeholder');
            
            if (isDisplayed && placeholder) {
              console.log(`   ✅ Found input with placeholder: "${placeholder}"`);
              chatInput = element;
              break;
            }
          }
          
          if (chatInput) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!chatInput) {
        console.log('   ❌ Could not find chat input');
        await this.takeScreenshot('04-no-chat-input');
        return;
      }
      
      // Step 5: Send Message
      console.log('\n📤 Step 5: Send Travel Request');
      console.log('━'.repeat(50));
      
      const message = "Create a 3-day travel plan to Paris, France";
      
      await chatInput.clear();
      await chatInput.sendKeys(message);
      console.log(`   ✅ Typed: "${message}"`);
      
      await this.takeScreenshot('05-message-typed');
      
      // Send the message
      await chatInput.sendKeys(Key.RETURN);
      console.log('   ✅ Message sent');
      
      // Step 6: Wait for Response
      console.log('\n⏳ Step 6: Wait for AI Response');
      console.log('━'.repeat(50));
      
      console.log('   Waiting 10 seconds for response...');
      await this.driver.sleep(10000);
      
      await this.takeScreenshot('06-after-wait');
      
      // Check page content
      const bodyText = await this.driver.findElement(By.tagName('body')).getText();
      
      if (bodyText.toLowerCase().includes('paris') || 
          bodyText.toLowerCase().includes('day 1') ||
          bodyText.toLowerCase().includes('flight')) {
        console.log('   ✅ Found travel content in response!');
      } else {
        console.log('   ⚠️  No travel content found yet');
      }
      
      console.log('\n✅ Test Completed!');
      
    } catch (error) {
      console.error('\n❌ Test Error:', error.message);
      await this.takeScreenshot('error');
    } finally {
      if (this.driver) {
        await this.driver.quit();
        console.log('\n🧹 Browser closed');
      }
    }
  }

  async takeScreenshot(name) {
    try {
      const dir = path.join(__dirname, 'screenshots', 'simple-test');
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      const screenshot = await this.driver.takeScreenshot();
      const filename = path.join(dir, `${name}-${Date.now()}.png`);
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`   📸 Screenshot: ${filename}`);
    } catch (e) {
      console.error(`   ❌ Screenshot failed: ${e.message}`);
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new SimpleTripPlanTest();
  test.run().catch(console.error);
}

module.exports = SimpleTripPlanTest;