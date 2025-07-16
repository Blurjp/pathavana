const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');
const config = require('./testConfig');

/**
 * Trip Plan Creation Test V2 - Using centralized config
 */
class TripPlanTestV2 {
  constructor() {
    this.driver = null;
    this.config = config;
    this.screenshotDir = path.join(__dirname, 'screenshots', `test-${Date.now()}`);
  }

  async setup() {
    console.log('🔧 Setting up test environment...');
    
    // Create screenshot directory
    if (!fs.existsSync(this.screenshotDir)) {
      fs.mkdirSync(this.screenshotDir, { recursive: true });
    }
    
    // Setup Chrome
    const options = new chrome.Options();
    this.config.chromeOptions.forEach(opt => options.addArguments(opt));
    
    this.driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
      
    await this.driver.manage().setTimeouts({ 
      implicit: this.config.timeouts.elementWait 
    });
    
    console.log('✅ Test environment ready');
  }

  async cleanup() {
    if (this.driver) {
      await this.driver.quit();
      console.log('🧹 Test cleanup complete');
    }
  }

  async takeScreenshot(name) {
    try {
      const screenshot = await this.driver.takeScreenshot();
      const filename = path.join(this.screenshotDir, `${name}.png`);
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`   📸 ${name}`);
    } catch (e) {
      console.error(`   ❌ Screenshot failed: ${e.message}`);
    }
  }

  async waitForElement(selector, timeout = this.config.timeouts.elementWait) {
    const element = await this.driver.wait(
      until.elementLocated(By.css(selector)),
      timeout
    );
    await this.driver.wait(until.elementIsVisible(element), timeout);
    return element;
  }

  async findElement(selectors) {
    const selectorArray = Array.isArray(selectors) ? selectors : [selectors];
    
    for (const selector of selectorArray) {
      try {
        const element = await this.driver.findElement(By.css(selector));
        if (await element.isDisplayed()) {
          return element;
        }
      } catch (e) {
        continue;
      }
    }
    
    throw new Error(`No element found for selectors: ${selectorArray.join(', ')}`);
  }

  async login() {
    console.log('\n🔐 Authentication');
    console.log('━'.repeat(50));
    
    // Navigate to homepage
    console.log('   📍 Navigating to homepage...');
    await this.driver.get(this.config.urls.frontend);
    await this.driver.wait(until.titleContains('Pathavana'), this.config.timeouts.pageLoad);
    
    // Check if already logged in
    try {
      await this.driver.findElement(By.css(this.config.selectors.userAvatar));
      console.log('   ✅ Already authenticated');
      await this.takeScreenshot('01-already-logged-in');
      return true;
    } catch (e) {
      // Not logged in, proceed with authentication
    }
    
    // Click Sign In
    console.log('   🔍 Finding Sign In button...');
    const signInButton = await this.findElement(this.config.selectors.signInButton);
    await signInButton.click();
    console.log('   ✅ Clicked Sign In');
    
    await this.driver.sleep(this.config.timeouts.animation);
    
    // Fill login form
    console.log('   📝 Filling login form...');
    const emailInput = await this.waitForElement(this.config.selectors.emailInput);
    await emailInput.clear();
    await emailInput.sendKeys(this.config.testUser.email);
    
    const passwordInput = await this.waitForElement(this.config.selectors.passwordInput);
    await passwordInput.clear();
    await passwordInput.sendKeys(this.config.testUser.password);
    
    console.log(`   📧 Email: ${this.config.testUser.email}`);
    console.log(`   🔑 Password: ${'*'.repeat(this.config.testUser.password.length)}`);
    
    // Submit
    await passwordInput.sendKeys(Key.RETURN);
    console.log('   ✅ Submitted login form');
    
    // Wait for authentication
    await this.driver.wait(
      until.elementLocated(By.css(this.config.selectors.userAvatar)),
      15000
    );
    
    await this.driver.sleep(2000); // Allow redirects
    console.log('   ✅ Authentication successful');
    await this.takeScreenshot('01-authenticated');
    
    return true;
  }

  async navigateToChat() {
    console.log('\n💬 Navigate to Chat');
    console.log('━'.repeat(50));
    
    const currentUrl = await this.driver.getCurrentUrl();
    
    if (currentUrl.includes('/chat')) {
      console.log('   ✅ Already on chat page');
    } else {
      try {
        const chatLink = await this.findElement(this.config.selectors.chatLink);
        await chatLink.click();
        console.log('   ✅ Clicked Chat link');
      } catch (e) {
        console.log('   📍 Direct navigation to /chat');
        await this.driver.get(`${this.config.urls.frontend}/chat`);
      }
      
      await this.driver.wait(until.urlContains('/chat'), this.config.timeouts.pageLoad);
    }
    
    await this.driver.sleep(this.config.timeouts.animation);
    console.log('   ✅ On chat page');
    await this.takeScreenshot('02-chat-page');
  }

  async sendTravelRequest() {
    console.log('\n📤 Send Travel Request');
    console.log('━'.repeat(50));
    
    // Find chat input
    const chatInput = await this.findElement(this.config.selectors.chatInput);
    console.log('   ✅ Found chat input');
    
    // Type message
    await chatInput.clear();
    await chatInput.sendKeys(this.config.testData.simpleRequest);
    console.log('   ✅ Typed travel request');
    await this.takeScreenshot('03-request-typed');
    
    // Send
    try {
      const sendButton = await this.findElement(this.config.selectors.sendButton);
      await sendButton.click();
      console.log('   ✅ Clicked send button');
    } catch (e) {
      await chatInput.sendKeys(Key.RETURN);
      console.log('   ✅ Sent via Enter key');
    }
  }

  async waitForResponse() {
    console.log('\n⏳ Wait for AI Response');
    console.log('━'.repeat(50));
    
    const startTime = Date.now();
    let responseFound = false;
    
    while (Date.now() - startTime < this.config.timeouts.aiResponse) {
      try {
        const messages = await this.driver.findElements(
          By.css(this.config.selectors.aiMessage.join(', '))
        );
        
        for (const message of messages) {
          const text = await message.getText();
          if (text && text.length > 50 && !text.includes('...')) {
            responseFound = true;
            console.log('   ✅ AI response received');
            console.log(`   📝 Preview: ${text.substring(0, 100)}...`);
            break;
          }
        }
        
        if (responseFound) break;
      } catch (e) {
        // Continue waiting
      }
      
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      if (elapsed % 10 === 0 && elapsed > 0) {
        console.log(`   ⏱️  ${elapsed}s elapsed...`);
      }
      
      await this.driver.sleep(1000);
    }
    
    if (!responseFound) {
      throw new Error('Timeout waiting for AI response');
    }
    
    await this.takeScreenshot('04-ai-response');
  }

  async verifyTripPlan() {
    console.log('\n✅ Verify Trip Plan');
    console.log('━'.repeat(50));
    
    await this.driver.sleep(3000); // Allow UI to update
    
    // Check for sidebar toggle
    try {
      const toggle = await this.driver.findElement(By.css(this.config.selectors.sidebarToggle));
      if (await toggle.isDisplayed()) {
        await toggle.click();
        console.log('   📂 Opened sidebar');
        await this.driver.sleep(this.config.timeouts.animation);
      }
    } catch (e) {
      // No toggle, continue
    }
    
    // Look for trip plan
    let planFound = false;
    try {
      const planElement = await this.findElement(this.config.selectors.tripPlanPanel);
      const text = await planElement.getText();
      
      if (text && text.length > 50) {
        planFound = true;
        console.log('   ✅ Trip plan found');
        console.log(`   📄 Content: ${text.substring(0, 200)}...`);
      }
    } catch (e) {
      // Check main content as fallback
      const body = await this.driver.findElement(By.tagName('body'));
      const text = await body.getText();
      
      if (text.toLowerCase().includes('day 1') || text.toLowerCase().includes('paris')) {
        planFound = true;
        console.log('   ✅ Trip plan found in main content');
      }
    }
    
    if (!planFound) {
      throw new Error('Trip plan not found');
    }
    
    await this.takeScreenshot('05-trip-plan');
  }

  async run() {
    console.log('\n🚀 Trip Plan Creation Test V2');
    console.log('═'.repeat(60));
    console.log(`📍 Frontend: ${this.config.urls.frontend}`);
    console.log(`📧 Test User: ${this.config.testUser.email}`);
    console.log(`📁 Screenshots: ${this.screenshotDir}`);
    console.log('═'.repeat(60));
    
    try {
      await this.setup();
      
      // Run test steps
      await this.login();
      await this.navigateToChat();
      await this.sendTravelRequest();
      await this.waitForResponse();
      await this.verifyTripPlan();
      
      console.log('\n✅ TEST PASSED');
      console.log('═'.repeat(60));
      await this.takeScreenshot('06-success');
      
    } catch (error) {
      console.error('\n❌ TEST FAILED');
      console.error(`Error: ${error.message}`);
      await this.takeScreenshot('error');
      throw error;
      
    } finally {
      await this.cleanup();
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new TripPlanTestV2();
  test.run()
    .then(() => {
      console.log('\n✅ Test completed successfully');
      process.exit(0);
    })
    .catch(err => {
      console.error('\n❌ Test failed:', err.message);
      process.exit(1);
    });
}

module.exports = TripPlanTestV2;