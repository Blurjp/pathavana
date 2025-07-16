const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

class PathavanaUITest {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000';
    this.testResults = [];
  }

  async setup() {
    console.log('🔧 Setting up Chrome driver...');
    
    const options = new chrome.Options();
    options.addArguments('--disable-dev-shm-usage');
    options.addArguments('--no-sandbox');
    options.addArguments('--window-size=1920,1080');
    // Uncomment to run headless
    // options.addArguments('--headless');
    
    this.driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
      
    console.log('✅ Chrome driver ready');
  }

  async cleanup() {
    if (this.driver) {
      await this.driver.quit();
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
      console.log(`📸 Screenshot saved: ${filename}`);
    } catch (e) {
      console.error('Failed to take screenshot:', e.message);
    }
  }

  async waitAndClick(selector, timeout = 10000) {
    // Handle multiple selectors
    const selectors = selector.split(',').map(s => s.trim());
    let element = null;
    let lastError = null;
    
    for (const sel of selectors) {
      try {
        element = await this.driver.wait(
          until.elementLocated(By.css(sel)),
          Math.min(2000, timeout) // Try each selector for 2 seconds
        );
        await this.driver.wait(until.elementIsVisible(element), 2000);
        await this.driver.wait(until.elementIsEnabled(element), 2000);
        break; // Found valid element
      } catch (e) {
        lastError = e;
        continue;
      }
    }
    
    if (!element) {
      throw lastError || new Error(`No element found for selectors: ${selector}`);
    }
    
    await element.click();
    return element;
  }

  async waitAndType(selector, text, timeout = 10000) {
    const element = await this.driver.wait(
      until.elementLocated(By.css(selector)),
      timeout
    );
    await this.driver.wait(until.elementIsVisible(element), timeout);
    await element.clear();
    await element.sendKeys(text);
    return element;
  }

  async login() {
    console.log('🔐 Attempting to login...');
    
    try {
      // Check if already logged in
      try {
        await this.driver.findElement(By.css('.user-avatar')).isDisplayed();
        console.log('✅ Already logged in');
        return;
      } catch (e) {
        // Not logged in, proceed with login
      }
      
      // Click Sign In button
      await this.waitAndClick('.auth-buttons button:first-child, button.btn-secondary');
      await this.driver.sleep(1000);
      
      // Fill login form
      await this.waitAndType('input[type="email"], input[name="email"]', 'test@example.com');
      await this.waitAndType('input[type="password"], input[name="password"]', 'testpassword');
      
      // Submit form
      const submitButton = await this.driver.findElement(
        By.xpath("//button[contains(text(),'Sign In') or contains(text(),'Sign in') or contains(text(),'Login')]")
      );
      await submitButton.click();
      
      // Wait for login to complete
      await this.driver.wait(
        until.elementLocated(By.css('.user-avatar, .avatar-placeholder')),
        15000
      );
      
      console.log('✅ Login successful');
      await this.driver.sleep(2000); // Give time for any redirects
    } catch (error) {
      console.error('❌ Login failed:', error.message);
      await this.takeScreenshot('login-error');
      throw error;
    }
  }

  async navigateToChat() {
    console.log('📍 Navigating to chat page...');
    
    const currentUrl = await this.driver.getCurrentUrl();
    if (!currentUrl.includes('/chat')) {
      // Try clicking Chat link in nav
      try {
        await this.waitAndClick('a[href="/chat"], .nav-menu a:first-child');
        await this.driver.wait(until.urlContains('/chat'), 10000);
      } catch (e) {
        // Direct navigation as fallback
        await this.driver.get(`${this.baseUrl}/chat`);
        await this.driver.wait(until.urlContains('/chat'), 10000);
      }
    }
    
    console.log('✅ On chat page');
    await this.driver.sleep(2000); // Let page fully load
  }

  async sendChatMessage(message) {
    console.log(`💬 Sending message: "${message}"`);
    
    try {
      // Find the chat input
      let chatInput = null;
      const inputSelectors = [
        'textarea[placeholder*="Type your message"]',
        'textarea[placeholder*="Ask me"]',
        '.chat-input textarea',
        '.chat-input input',
        'textarea',
        'input[type="text"]:not([type="email"]):not([type="password"])'
      ];
      
      for (const selector of inputSelectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          for (const element of elements) {
            if (await element.isDisplayed() && await element.isEnabled()) {
              const placeholder = await element.getAttribute('placeholder');
              if (placeholder && (placeholder.toLowerCase().includes('message') || 
                                placeholder.toLowerCase().includes('ask'))) {
                chatInput = element;
                break;
              }
            }
          }
          if (chatInput) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!chatInput) {
        // Try a more general approach
        const textareas = await this.driver.findElements(By.tagName('textarea'));
        for (const textarea of textareas) {
          if (await textarea.isDisplayed() && await textarea.isEnabled()) {
            chatInput = textarea;
            break;
          }
        }
      }
      
      if (!chatInput) {
        throw new Error('Could not find chat input');
      }
      
      await chatInput.clear();
      await chatInput.sendKeys(message);
      
      // Send the message
      // Try to find send button first
      let sent = false;
      try {
        const sendButton = await this.driver.findElement(
          By.css('button[type="submit"], .chat-input button, button[aria-label*="send"]')
        );
        if (await sendButton.isEnabled()) {
          await sendButton.click();
          sent = true;
        }
      } catch (e) {
        // Button not found
      }
      
      // If no button found or click failed, try Enter key
      if (!sent) {
        await chatInput.sendKeys(Key.RETURN);
      }
      
      console.log('✅ Message sent');
      await this.driver.sleep(1000);
      
    } catch (error) {
      console.error('❌ Failed to send message:', error.message);
      await this.takeScreenshot('send-message-error');
      throw error;
    }
  }

  async waitForAIResponse(timeout = 60000) {
    console.log('⏳ Waiting for AI response...');
    
    const startTime = Date.now();
    
    try {
      await this.driver.wait(async () => {
        // Look for AI/assistant messages
        const messageSelectors = [
          '.message-content.assistant',
          '.chat-message.assistant',
          '.message.assistant',
          '[data-role="assistant"]',
          '.ai-message',
          '.bot-message'
        ];
        
        for (const selector of messageSelectors) {
          try {
            const messages = await this.driver.findElements(By.css(selector));
            if (messages.length > 0) {
              const lastMessage = messages[messages.length - 1];
              const text = await lastMessage.getText();
              
              // Check if message is complete (not loading)
              if (text && text.length > 20 && 
                  !text.includes('...') && 
                  !text.includes('typing') &&
                  !text.includes('thinking')) {
                return true;
              }
            }
          } catch (e) {
            continue;
          }
        }
        
        // Also check for any message that contains travel-related keywords
        try {
          const allMessages = await this.driver.findElements(By.css('.message, .chat-message'));
          for (const msg of allMessages) {
            const text = await msg.getText();
            if (text.toLowerCase().includes('day 1') || 
                text.toLowerCase().includes('itinerary') ||
                text.toLowerCase().includes('flight')) {
              return true;
            }
          }
        } catch (e) {
          // Continue waiting
        }
        
        return false;
      }, timeout);
      
      const duration = Date.now() - startTime;
      console.log(`✅ AI response received in ${duration}ms`);
      
    } catch (error) {
      console.error('❌ Timeout waiting for AI response');
      await this.takeScreenshot('ai-response-timeout');
      throw new Error('AI response timeout');
    }
  }

  async checkTravelPlanPanel() {
    console.log('🔍 Checking for travel plan in side panel...');
    
    try {
      // First, check if there's a toggle button for the sidebar
      try {
        const toggleButton = await this.driver.findElement(
          By.css('.sidebar-toggle, button[aria-label*="sidebar"], button[aria-label*="panel"]')
        );
        if (await toggleButton.isDisplayed()) {
          const isActive = (await toggleButton.getAttribute('class')).includes('active');
          if (!isActive) {
            console.log('📂 Opening sidebar...');
            await toggleButton.click();
            await this.driver.sleep(1000);
          }
        }
      } catch (e) {
        // No toggle button, sidebar might be always visible
      }
      
      // Look for travel plan content
      const panelSelectors = [
        '.trip-plan-panel',
        '.travel-plan',
        '.sidebar-content',
        '.search-results-sidebar',
        '[class*="sidebar"]',
        '[class*="panel"]'
      ];
      
      for (const selector of panelSelectors) {
        try {
          const panels = await this.driver.findElements(By.css(selector));
          for (const panel of panels) {
            if (await panel.isDisplayed()) {
              const text = await panel.getText();
              
              // Check for travel-related content
              const hasTravel = ['day', 'flight', 'hotel', 'itinerary', 'travel', 'trip']
                .some(keyword => text.toLowerCase().includes(keyword));
                
              if (hasTravel) {
                console.log(`✅ Found travel plan in ${selector}`);
                console.log(`📄 Content preview: ${text.substring(0, 200)}...`);
                
                // Take screenshot of success
                await this.takeScreenshot('travel-plan-found');
                
                // Check for specific elements
                const hasFlights = text.toLowerCase().includes('flight');
                const hasHotels = text.toLowerCase().includes('hotel');
                const hasItinerary = text.toLowerCase().includes('day');
                
                console.log(`  - Flights: ${hasFlights ? '✅' : '❌'}`);
                console.log(`  - Hotels: ${hasHotels ? '✅' : '❌'}`);
                console.log(`  - Itinerary: ${hasItinerary ? '✅' : '❌'}`);
                
                return true;
              }
            }
          }
        } catch (e) {
          continue;
        }
      }
      
      // If not in sidebar, check main content
      console.log('⚠️ Travel plan not found in sidebar, checking main content...');
      const mainContent = await this.driver.findElement(By.css('body')).getText();
      if (mainContent.toLowerCase().includes('day 1') || 
          mainContent.toLowerCase().includes('itinerary')) {
        console.log('✅ Travel plan found in main content');
        return true;
      }
      
      return false;
      
    } catch (error) {
      console.error('❌ Error checking travel plan:', error.message);
      await this.takeScreenshot('travel-plan-error');
      return false;
    }
  }

  async runTest(name, testFn) {
    console.log(`\n🧪 Test: ${name}`);
    console.log('─'.repeat(50));
    
    const startTime = Date.now();
    try {
      await testFn();
      const duration = Date.now() - startTime;
      this.testResults.push({ name, status: 'PASS', duration });
      console.log(`✅ PASSED (${duration}ms)`);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.testResults.push({ name, status: 'FAIL', duration, error: error.message });
      console.log(`❌ FAILED (${duration}ms): ${error.message}`);
      throw error;
    }
  }

  async runAllTests() {
    console.log('🚀 Pathavana UI Test Suite');
    console.log('═'.repeat(50));
    console.log(`📍 Target: ${this.baseUrl}`);
    console.log(`🕐 Started: ${new Date().toLocaleString()}`);
    console.log('═'.repeat(50));
    
    try {
      await this.setup();
      
      // Test 1: Load homepage
      await this.runTest('Load Homepage', async () => {
        await this.driver.get(this.baseUrl);
        await this.driver.wait(until.titleContains('Pathavana'), 10000);
        const title = await this.driver.getTitle();
        console.log(`  Page title: ${title}`);
      });
      
      // Test 2: Login
      await this.runTest('User Authentication', async () => {
        await this.login();
      });
      
      // Test 3: Navigate to chat
      await this.runTest('Navigate to Chat', async () => {
        await this.navigateToChat();
      });
      
      // Test 4: Send travel request
      await this.runTest('Send Travel Planning Request', async () => {
        const message = "Create a 3-day travel itinerary for Paris, France. Include flights from New York, hotel suggestions near the Eiffel Tower, and must-see attractions with a daily schedule.";
        await this.sendChatMessage(message);
      });
      
      // Test 5: Wait for AI response
      await this.runTest('AI Response Generation', async () => {
        await this.waitForAIResponse(60000);
      });
      
      // Test 6: Verify travel plan display
      await this.runTest('Travel Plan Display Verification', async () => {
        await this.driver.sleep(3000); // Give UI time to update
        const found = await this.checkTravelPlanPanel();
        if (!found) {
          throw new Error('Travel plan not displayed in side panel');
        }
      });
      
    } catch (error) {
      console.error('\n💥 Test suite failed:', error.message);
    } finally {
      // Print summary
      console.log('\n═'.repeat(50));
      console.log('📊 Test Summary');
      console.log('═'.repeat(50));
      
      let passed = 0;
      let failed = 0;
      
      this.testResults.forEach(result => {
        const icon = result.status === 'PASS' ? '✅' : '❌';
        console.log(`${icon} ${result.name} (${result.duration}ms)`);
        if (result.error) {
          console.log(`   └─ ${result.error}`);
        }
        
        if (result.status === 'PASS') passed++;
        else failed++;
      });
      
      console.log('─'.repeat(50));
      console.log(`Total: ${this.testResults.length} | ✅ Passed: ${passed} | ❌ Failed: ${failed}`);
      console.log(`Success Rate: ${((passed / this.testResults.length) * 100).toFixed(1)}%`);
      console.log(`🏁 Completed: ${new Date().toLocaleString()}`);
      
      await this.cleanup();
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new PathavanaUITest();
  test.runAllTests().catch(console.error);
}

module.exports = PathavanaUITest;