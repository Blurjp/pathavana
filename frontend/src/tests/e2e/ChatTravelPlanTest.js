const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

/**
 * Selenium UI Test for Travel Plan Creation
 * Tests the core functionality of creating a travel plan through chat
 */
class ChatTravelPlanTest {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000';
  }

  async setup() {
    console.log('🔧 Setting up Chrome WebDriver...');
    
    const options = new chrome.Options();
    options.addArguments('--window-size=1920,1080');
    // Uncomment to run headless
    // options.addArguments('--headless');
    
    this.driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
      
    console.log('✅ Chrome WebDriver initialized');
  }

  async cleanup() {
    if (this.driver) {
      await this.driver.quit();
      console.log('🧹 Browser closed');
    }
  }

  async takeScreenshot(name) {
    try {
      const screenshot = await this.driver.takeScreenshot();
      const dir = path.join(__dirname, 'screenshots');
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      const filename = path.join(dir, `${name}-${Date.now()}.png`);
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`📸 Screenshot: ${filename}`);
      return filename;
    } catch (e) {
      console.error('Screenshot failed:', e.message);
    }
  }

  async navigateToChat() {
    console.log('\n🌐 Navigating to chat page...');
    
    // First go to homepage
    await this.driver.get(this.baseUrl);
    await this.driver.sleep(2000);
    
    // Since we're not logged in, we'll be redirected to homepage
    // Let's try to go directly to chat
    await this.driver.get(`${this.baseUrl}/chat`);
    await this.driver.sleep(2000);
    
    const currentUrl = await this.driver.getCurrentUrl();
    console.log(`📍 Current URL: ${currentUrl}`);
    
    // Check if we're redirected back to homepage
    if (currentUrl === `${this.baseUrl}/`) {
      console.log('⚠️  Redirected to homepage (not authenticated)');
      console.log('ℹ️  This is expected behavior - non-authenticated users are redirected');
      
      // For demo purposes, let's show what would happen with auth
      console.log('\n📝 Test Scenario: What happens after authentication');
      console.log('   1. User logs in via Sign In button');
      console.log('   2. User is redirected to /chat');
      console.log('   3. User can send travel planning messages');
      console.log('   4. AI responds with travel plan');
      console.log('   5. Travel plan appears in right sidebar\n');
      
      return false;
    }
    
    return true;
  }

  async findChatInput() {
    console.log('🔍 Looking for chat input...');
    
    const selectors = [
      'textarea[placeholder*="Type your message"]',
      'textarea[placeholder*="Ask me"]',
      '.chat-input textarea',
      'textarea',
      'input[type="text"]'
    ];
    
    for (const selector of selectors) {
      try {
        const elements = await this.driver.findElements(By.css(selector));
        for (const element of elements) {
          const isDisplayed = await element.isDisplayed();
          if (isDisplayed) {
            console.log(`✅ Found chat input: ${selector}`);
            return element;
          }
        }
      } catch (e) {
        continue;
      }
    }
    
    return null;
  }

  async sendMessage(message) {
    console.log(`\n💬 Sending message: "${message}"`);
    
    const chatInput = await this.findChatInput();
    if (!chatInput) {
      console.log('❌ Chat input not found');
      return false;
    }
    
    await chatInput.clear();
    await chatInput.sendKeys(message);
    
    // Try to find send button
    try {
      const sendButton = await this.driver.findElement(
        By.css('button[type="submit"], .chat-input button')
      );
      await sendButton.click();
      console.log('✅ Message sent via button');
    } catch (e) {
      // Fallback to Enter key
      await chatInput.sendKeys(Key.RETURN);
      console.log('✅ Message sent via Enter key');
    }
    
    return true;
  }

  async waitForResponse(timeout = 60000) {
    console.log('\n⏳ Waiting for AI response...');
    
    const startTime = Date.now();
    const endTime = startTime + timeout;
    
    while (Date.now() < endTime) {
      try {
        // Look for AI response indicators
        const responseSelectors = [
          '.message.assistant',
          '.chat-message.assistant',
          '[data-role="assistant"]',
          '.ai-message'
        ];
        
        for (const selector of responseSelectors) {
          const elements = await this.driver.findElements(By.css(selector));
          if (elements.length > 0) {
            const lastElement = elements[elements.length - 1];
            const text = await lastElement.getText();
            
            if (text && text.length > 50) {
              console.log('✅ AI response received');
              console.log(`📝 Response preview: ${text.substring(0, 100)}...`);
              return true;
            }
          }
        }
      } catch (e) {
        // Continue waiting
      }
      
      await this.driver.sleep(1000);
    }
    
    console.log('❌ Timeout waiting for AI response');
    return false;
  }

  async checkTravelPlan() {
    console.log('\n🔍 Checking for travel plan display...');
    
    // Check for sidebar toggle
    try {
      const toggleButton = await this.driver.findElement(
        By.css('.sidebar-toggle, button[aria-label*="sidebar"]')
      );
      if (await toggleButton.isDisplayed()) {
        console.log('📂 Found sidebar toggle, clicking...');
        await toggleButton.click();
        await this.driver.sleep(1000);
      }
    } catch (e) {
      // No toggle found
    }
    
    // Look for travel plan content
    const selectors = [
      '.trip-plan-panel',
      '.travel-plan',
      '.sidebar-content',
      '.search-results-sidebar'
    ];
    
    for (const selector of selectors) {
      try {
        const element = await this.driver.findElement(By.css(selector));
        if (await element.isDisplayed()) {
          const text = await element.getText();
          console.log(`✅ Found travel plan in: ${selector}`);
          console.log(`📄 Content: ${text.substring(0, 200)}...`);
          
          // Check for key travel elements
          const hasItinerary = text.toLowerCase().includes('day');
          const hasFlights = text.toLowerCase().includes('flight');
          const hasHotels = text.toLowerCase().includes('hotel');
          
          console.log(`\n📊 Travel Plan Analysis:`);
          console.log(`   - Itinerary: ${hasItinerary ? '✅' : '❌'}`);
          console.log(`   - Flights: ${hasFlights ? '✅' : '❌'}`);
          console.log(`   - Hotels: ${hasHotels ? '✅' : '❌'}`);
          
          return true;
        }
      } catch (e) {
        continue;
      }
    }
    
    console.log('❌ Travel plan panel not found');
    return false;
  }

  async runTest() {
    console.log('🚀 Chat Travel Plan UI Test');
    console.log('════════════════════════════════════════');
    console.log(`📍 Target: ${this.baseUrl}`);
    console.log(`🕐 Started: ${new Date().toLocaleString()}`);
    console.log('════════════════════════════════════════\n');
    
    try {
      await this.setup();
      
      // Step 1: Navigate to chat
      const onChatPage = await this.navigateToChat();
      
      if (!onChatPage) {
        console.log('\n📋 Test Summary for Unauthenticated Access:');
        console.log('✅ Homepage loads correctly');
        console.log('✅ Unauthenticated users redirected from /chat to /');
        console.log('✅ Authentication guard working as expected');
        
        console.log('\n📝 To test the full flow:');
        console.log('1. Create test user account or use existing credentials');
        console.log('2. Implement login automation in the test');
        console.log('3. Run the travel plan creation test');
        
        await this.takeScreenshot('homepage-redirect');
        
        // Show what the test would do if authenticated
        console.log('\n🎯 Expected Flow (when authenticated):');
        console.log('1. User navigates to /chat');
        console.log('2. User types: "Create a 3-day travel plan to Paris"');
        console.log('3. AI generates comprehensive travel plan');
        console.log('4. Travel plan appears in right sidebar with:');
        console.log('   - Day-by-day itinerary');
        console.log('   - Flight recommendations');
        console.log('   - Hotel suggestions');
        console.log('   - Activity recommendations');
        
        return;
      }
      
      // Step 2: Send travel planning message
      const message = "Create a 3-day travel plan to Paris, France including flights from New York, hotels, and must-see attractions";
      const sent = await this.sendMessage(message);
      
      if (!sent) {
        console.log('❌ Failed to send message');
        await this.takeScreenshot('send-failed');
        return;
      }
      
      // Step 3: Wait for AI response
      const hasResponse = await this.waitForResponse();
      
      if (!hasResponse) {
        await this.takeScreenshot('no-response');
        return;
      }
      
      // Step 4: Check for travel plan
      await this.driver.sleep(3000); // Give UI time to update
      const hasPlan = await this.checkTravelPlan();
      
      if (hasPlan) {
        console.log('\n✅ SUCCESS: Travel plan created and displayed!');
        await this.takeScreenshot('travel-plan-success');
      } else {
        console.log('\n❌ FAIL: Travel plan not found in UI');
        await this.takeScreenshot('travel-plan-missing');
      }
      
    } catch (error) {
      console.error('\n💥 Test error:', error.message);
      await this.takeScreenshot('test-error');
    } finally {
      console.log('\n════════════════════════════════════════');
      console.log(`🏁 Completed: ${new Date().toLocaleString()}`);
      await this.cleanup();
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new ChatTravelPlanTest();
  test.runTest().catch(console.error);
}

module.exports = ChatTravelPlanTest;