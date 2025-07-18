const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

/**
 * Complete UI Test for Trip Plan Creation via AI Chat
 * This test logs in, navigates to chat, sends a travel request, and verifies the trip plan
 */
class TripPlanCreationTest {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000'; // Note: Use http, not https for local development
    this.testResults = [];
    this.screenshotDir = path.join(__dirname, 'screenshots', `test-run-${Date.now()}`);
  }

  async setup() {
    console.log('🔧 Setting up Chrome WebDriver...');
    
    // Create screenshot directory
    if (!fs.existsSync(this.screenshotDir)) {
      fs.mkdirSync(this.screenshotDir, { recursive: true });
    }
    
    const options = new chrome.Options();
    options.addArguments('--window-size=1920,1080');
    options.addArguments('--disable-dev-shm-usage');
    options.addArguments('--no-sandbox');
    options.addArguments('--disable-gpu'); // Help with stability
    options.addArguments('--disable-web-security'); // For local testing
    options.addArguments('--disable-features=VizDisplayCompositor');
    // Uncomment for headless mode
    // options.addArguments('--headless');
    
    this.driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
      
    // Set implicit wait
    await this.driver.manage().setTimeouts({ implicit: 5000 });
      
    console.log('✅ Chrome WebDriver ready');
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
      const filename = path.join(this.screenshotDir, `${name}.png`);
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`   📸 Screenshot: ${filename}`);
      return filename;
    } catch (e) {
      console.error('   ❌ Screenshot failed:', e.message);
    }
  }

  async waitForElement(selector, timeout = 10000) {
    try {
      const element = await this.driver.wait(
        until.elementLocated(By.css(selector)),
        timeout,
        `Timeout waiting for element: ${selector}`
      );
      await this.driver.wait(
        until.elementIsVisible(element),
        timeout,
        `Element not visible: ${selector}`
      );
      return element;
    } catch (e) {
      await this.takeScreenshot(`error-element-not-found-${Date.now()}`);
      throw e;
    }
  }

  async login(email = 'selenium.test@example.com', password = 'SeleniumTest123!') {
    console.log('\n🔐 Step 1: User Authentication');
    console.log('━'.repeat(50));
    
    try {
      // First navigate to the homepage
      console.log('   📍 Navigating to homepage...');
      await this.driver.get(this.baseUrl);
      
      // Wait for page to load and verify we're on the right page
      await this.driver.wait(until.titleContains('Pathavana'), 10000);
      const currentUrl = await this.driver.getCurrentUrl();
      console.log(`   📍 Current URL: ${currentUrl}`);
      
      if (!currentUrl.startsWith(this.baseUrl)) {
        throw new Error(`Navigation failed. Expected ${this.baseUrl}, got ${currentUrl}`);
      }
      
      await this.driver.sleep(1000); // Give page time to fully render
      
      // Check if already logged in
      try {
        const userAvatar = await this.driver.findElement(By.css('.user-avatar'));
        if (await userAvatar.isDisplayed()) {
          console.log('   ✅ Already logged in');
          return true;
        }
      } catch (e) {
        // Not logged in, proceed
      }
      
      console.log('   🔍 Finding Sign In button...');
      
      // Click Sign In button - try multiple selectors
      const signInSelectors = [
        '.auth-buttons button:first-child',
        'button.btn-secondary',
        'button:contains("Sign In")',
        'button[type="button"]'
      ];
      
      let signInClicked = false;
      for (const selector of signInSelectors) {
        try {
          const buttons = await this.driver.findElements(By.css(selector));
          for (const button of buttons) {
            const text = await button.getText();
            if (text.toLowerCase().includes('sign in')) {
              await button.click();
              signInClicked = true;
              console.log('   ✅ Clicked Sign In button');
              break;
            }
          }
          if (signInClicked) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!signInClicked) {
        throw new Error('Could not find Sign In button');
      }
      
      // Wait for login modal
      await this.driver.sleep(1000);
      console.log('   ⏳ Waiting for login modal...');
      
      // Find and fill email field
      const emailInput = await this.waitForElement('input[type="email"], input[name="email"], input[placeholder*="email" i]');
      await emailInput.clear();
      await emailInput.sendKeys(email);
      console.log('   ✅ Entered email');
      
      // Find and fill password field
      const passwordInput = await this.waitForElement('input[type="password"], input[name="password"]');
      await passwordInput.clear();
      await passwordInput.sendKeys(password);
      console.log('   ✅ Entered password');
      
      // Submit login form
      const submitSelectors = [
        'button[type="submit"]',
        'button.btn-primary',
        'button'
      ];
      
      let submitted = false;
      for (const selector of submitSelectors) {
        try {
          const buttons = await this.driver.findElements(By.css(selector));
          for (const button of buttons) {
            const text = await button.getText();
            if (text.toLowerCase().includes('sign in') || 
                text.toLowerCase().includes('login') ||
                text.toLowerCase().includes('submit')) {
              await button.click();
              submitted = true;
              console.log('   ✅ Submitted login form');
              break;
            }
          }
          if (submitted) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!submitted) {
        // Try pressing Enter as fallback
        await passwordInput.sendKeys(Key.RETURN);
        console.log('   ✅ Submitted via Enter key');
      }
      
      // Wait for authentication to complete
      console.log('   ⏳ Waiting for authentication...');
      await this.driver.wait(
        until.elementLocated(By.css('.user-avatar, .avatar-placeholder')),
        15000,
        'Login timeout - user avatar not found'
      );
      
      await this.driver.sleep(2000); // Give time for any redirects
      console.log('   ✅ Authentication successful!');
      
      await this.takeScreenshot('01-logged-in');
      return true;
      
    } catch (error) {
      console.error('   ❌ Login failed:', error.message);
      await this.takeScreenshot('login-error');
      throw error;
    }
  }

  async navigateToChat() {
    console.log('\n📍 Step 2: Navigate to Chat');
    console.log('━'.repeat(50));
    
    try {
      const currentUrl = await this.driver.getCurrentUrl();
      console.log(`   📍 Current URL: ${currentUrl}`);
      
      if (!currentUrl.includes('/chat')) {
        // Try clicking Chat link in navigation
        try {
          console.log('   🔍 Looking for Chat navigation link...');
          const chatLink = await this.waitForElement('a[href="/chat"], .nav-menu a:first-child', 5000);
          await chatLink.click();
          console.log('   ✅ Clicked Chat link');
        } catch (e) {
          // Direct navigation as fallback
          console.log('   📍 Navigating directly to /chat...');
          await this.driver.get(`${this.baseUrl}/chat`);
        }
        
        // Wait for navigation
        await this.driver.wait(
          until.urlContains('/chat'),
          10000,
          'Navigation to chat page failed'
        );
      }
      
      await this.driver.sleep(2000); // Let page fully load
      console.log('   ✅ Successfully on chat page');
      
      await this.takeScreenshot('02-chat-page');
      return true;
      
    } catch (error) {
      console.error('   ❌ Navigation failed:', error.message);
      await this.takeScreenshot('navigation-error');
      throw error;
    }
  }

  async sendTravelRequest() {
    console.log('\n💬 Step 3: Send Travel Planning Request');
    console.log('━'.repeat(50));
    
    const travelRequest = "Create a comprehensive 5-day travel plan to Tokyo, Japan. I'm flying from San Francisco. " +
                         "Please include flight options, hotel recommendations in Shibuya area, " +
                         "and a daily itinerary with must-see attractions, local restaurants, and cultural experiences. " +
                         "My budget is around $3000 per person.";
    
    try {
      console.log('   🔍 Looking for chat input field...');
      
      // Find chat input with multiple selectors
      let chatInput = null;
      const inputSelectors = [
        'textarea[placeholder*="Type your message"]',
        'textarea[placeholder*="Ask me"]',
        'textarea[placeholder*="travel"]',
        '.chat-input textarea',
        '.chat-input input',
        'textarea',
        'input[type="text"]'
      ];
      
      for (const selector of inputSelectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          for (const element of elements) {
            if (await element.isDisplayed() && await element.isEnabled()) {
              const tagName = await element.getTagName();
              const type = await element.getAttribute('type');
              const placeholder = await element.getAttribute('placeholder');
              
              // Check if it's likely a chat input
              if ((tagName === 'textarea') || 
                  (tagName === 'input' && type !== 'email' && type !== 'password' && placeholder)) {
                chatInput = element;
                console.log(`   ✅ Found chat input: ${selector}`);
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
        throw new Error('Chat input field not found');
      }
      
      // Clear and type message
      await chatInput.clear();
      console.log('   📝 Typing travel request...');
      await chatInput.sendKeys(travelRequest);
      
      await this.takeScreenshot('03-message-typed');
      
      // Send the message
      console.log('   🚀 Sending message...');
      
      // Try to find send button
      let sent = false;
      const buttonSelectors = [
        'button[type="submit"]',
        'button[aria-label*="send" i]',
        '.chat-input button',
        'button.send-button'
      ];
      
      for (const selector of buttonSelectors) {
        try {
          const buttons = await this.driver.findElements(By.css(selector));
          for (const button of buttons) {
            if (await button.isDisplayed() && await button.isEnabled()) {
              // Check if it's near the chat input
              const buttonLocation = await button.getRect();
              const inputLocation = await chatInput.getRect();
              
              // Button should be close to input (within 200px)
              if (Math.abs(buttonLocation.y - inputLocation.y) < 200) {
                await button.click();
                sent = true;
                console.log('   ✅ Clicked send button');
                break;
              }
            }
          }
          if (sent) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!sent) {
        // Fallback to Enter key
        await chatInput.sendKeys(Key.RETURN);
        console.log('   ✅ Sent via Enter key');
      }
      
      console.log('   ✅ Travel request sent successfully!');
      return true;
      
    } catch (error) {
      console.error('   ❌ Failed to send message:', error.message);
      await this.takeScreenshot('send-error');
      throw error;
    }
  }

  async waitForAIResponse() {
    console.log('\n🤖 Step 4: Wait for AI Response');
    console.log('━'.repeat(50));
    
    try {
      console.log('   ⏳ Waiting for AI to generate travel plan...');
      
      const startTime = Date.now();
      const timeout = 90000; // 90 seconds for complex request
      
      // Wait for AI response to appear
      let responseFound = false;
      let lastMessageCount = 0;
      let debugCounter = 0;
      
      while (Date.now() - startTime < timeout) {
        // First try to find messages by class selectors
        const messageSelectors = [
          '.enhanced-chat-message.agent',
          '.message-content.assistant',
          '.chat-message.assistant',
          '.message.assistant',
          '[data-role="assistant"]',
          '.ai-message',
          '.bot-message',
          '.assistant-message',
          '.agent-message'
        ];
        
        for (const selector of messageSelectors) {
          try {
            const messages = await this.driver.findElements(By.css(selector));
            
            if (messages.length > lastMessageCount) {
              const lastMessage = messages[messages.length - 1];
              const text = await lastMessage.getText();
              
              // Check if we have any AI response
              if (text && text.length > 10) {
                // Accept short responses like "How can I help you plan your trip?"
                const aiKeywords = ['help', 'plan', 'trip', 'travel', 'assist', 'can i', 'how can'];
                const hasAIResponse = aiKeywords.some(keyword => 
                  text.toLowerCase().includes(keyword)
                );
                
                // Also check for travel-related content
                const travelKeywords = ['day', 'flight', 'hotel', 'tokyo', 'itinerary', 'attraction', 'restaurant'];
                const hasTravel = travelKeywords.some(keyword => 
                  text.toLowerCase().includes(keyword)
                );
                
                if (hasAIResponse || hasTravel) {
                  // Check if still loading (no ellipsis or loading indicators)
                  if (!text.includes('typing') && !text.includes('generating')) {
                    responseFound = true;
                    console.log('   ✅ AI response received!');
                    console.log(`   📄 Response preview: ${text.substring(0, 150)}...`);
                    break;
                  }
                }
              }
              
              lastMessageCount = messages.length;
            }
          } catch (e) {
            continue;
          }
        }
        
        if (responseFound) break;
        
        // Fallback: Look for bot icon or assistant message indicator
        if (!responseFound) {
          try {
            // Look for the bot assistant icon (shows as a circle with waves)
            const botIcons = await this.driver.findElements(By.css('.bot-icon, [class*="assistant"], img[alt*="assistant"], img[alt*="bot"]'));
            if (botIcons.length > 0) {
              // Get the message next to the bot icon
              for (const icon of botIcons) {
                try {
                  const parent = await icon.findElement(By.xpath("../.."));
                  const messageText = await parent.getText();
                  if (messageText && messageText.length > 10) {
                    responseFound = true;
                    console.log('   ✅ AI response found via bot icon!');
                    console.log(`   📄 Response preview: ${messageText.substring(0, 150)}...`);
                    break;
                  }
                } catch (e) {
                  continue;
                }
              }
            }
          } catch (e) {
            // Continue if search fails
          }
        }
        
        // Debug: Show what's on the page every 10 seconds
        debugCounter++;
        if (debugCounter % 10 === 0) {
          try {
            const allDivs = await this.driver.findElements(By.css('div'));
            console.log(`   🔍 Debug: Found ${allDivs.length} div elements on page`);
            
            // Check for any message-like content
            const messageDivs = await this.driver.findElements(By.css('[class*="message"], [class*="chat"]'));
            console.log(`   🔍 Debug: Found ${messageDivs.length} message/chat elements`);
            
            if (messageDivs.length > 0) {
              const lastDiv = messageDivs[messageDivs.length - 1];
              const className = await lastDiv.getAttribute('class');
              const text = await lastDiv.getText();
              console.log(`   🔍 Debug: Last message class: ${className}`);
              console.log(`   🔍 Debug: Last message preview: ${text.substring(0, 100)}...`);
            }
          } catch (e) {
            // Continue
          }
        }
        
        // Show progress
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (elapsed % 5 === 0 && elapsed > 0) {
          console.log(`   ⏱️  ${elapsed} seconds elapsed...`);
        }
        
        await this.driver.sleep(1000);
      }
      
      if (!responseFound) {
        throw new Error('Timeout waiting for AI response');
      }
      
      const duration = Math.floor((Date.now() - startTime) / 1000);
      console.log(`   ⏱️  Total response time: ${duration} seconds`);
      
      await this.takeScreenshot('04-ai-response');
      return true;
      
    } catch (error) {
      console.error('   ❌ AI response error:', error.message);
      await this.takeScreenshot('ai-response-error');
      throw error;
    }
  }

  async verifyTripPlan() {
    console.log('\n📋 Step 5: Verify Trip Plan Display');
    console.log('━'.repeat(50));
    
    try {
      // Give UI time to render the trip plan
      await this.driver.sleep(3000);
      
      // First ensure the sidebar is open
      console.log('   🔍 Looking for trip plan in sidebar...');
      
      // Find and click sidebar toggle if needed
      let sidebarOpened = false;
      const toggleSelectors = [
        'button[aria-label*="sidebar"]',
        'button[aria-label*="results"]',
        '.sidebar-toggle',
        '[data-testid="sidebar-toggle"]',
        'button[title*="sidebar"]',
        '.toggle-sidebar',
        '.hamburger-menu'
      ];
      
      for (const selector of toggleSelectors) {
        try {
          const toggleButton = await this.driver.findElement(By.css(selector));
          if (await toggleButton.isDisplayed()) {
            console.log(`   📂 Found sidebar toggle: ${selector}`);
            await toggleButton.click();
            sidebarOpened = true;
            await this.driver.sleep(1500); // Give sidebar time to animate open
            break;
          }
        } catch (e) {
          continue;
        }
      }
      
      if (!sidebarOpened) {
        console.log('   ⚠️  No sidebar toggle found - checking if sidebar is already visible');
      }
      
      // Verify sidebar is now visible
      let sidebarVisible = false;
      const sidebarSelectors = [
        '.search-results-sidebar',
        '.sidebar-container',
        '[class*="sidebar"][class*="open"]',
        '[class*="sidebar"][class*="visible"]',
        '.trip-plan-container'
      ];
      
      for (const selector of sidebarSelectors) {
        try {
          const sidebar = await this.driver.findElement(By.css(selector));
          if (await sidebar.isDisplayed()) {
            sidebarVisible = true;
            console.log(`   ✅ Sidebar is visible: ${selector}`);
            break;
          }
        } catch (e) {
          continue;
        }
      }
      
      if (!sidebarVisible) {
        console.log('   ❌ Sidebar not visible!');
        await this.takeScreenshot('sidebar-not-visible');
      }
      
      // Look for trip plan content IN THE SIDEBAR ONLY
      const planSelectors = [
        '.trip-plan-panel',  // Main trip plan panel component
        '.TripPlanPanel',
        '[class*="trip-plan-panel"]',
        '.search-results-sidebar .trip-plan',
        '.sidebar-content .trip-plan',
        '[data-testid="trip-plan-panel"]',
        '.plan-days',  // Trip plan days container
        '.plan-day',   // Individual day sections
        '.trip-itinerary'
      ];
      
      let tripPlanFound = false;
      let planContent = '';
      
      for (const selector of planSelectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          
          for (const element of elements) {
            if (await element.isDisplayed()) {
              const text = await element.getText();
              
              // Verify it contains trip plan content
              if (text && text.length > 50) {
                const hasDays = /day\s*\d/i.test(text);
                const hasFlights = text.toLowerCase().includes('flight');
                const hasHotels = text.toLowerCase().includes('hotel');
                const hasTokyo = text.toLowerCase().includes('tokyo');
                
                if (hasDays || hasFlights || hasHotels || hasTokyo) {
                  tripPlanFound = true;
                  planContent = text;
                  console.log(`   ✅ Found trip plan in: ${selector}`);
                  break;
                }
              }
            }
          }
          
          if (tripPlanFound) break;
        } catch (e) {
          continue;
        }
      }
      
      if (!tripPlanFound) {
        // The trip plan MUST be in the sidebar, NOT in chat messages
        console.log('   ❌ Trip plan NOT found in sidebar!');
        console.log('   📍 The trip plan should appear in the right sidebar panel');
        
        // Take a screenshot to debug
        await this.takeScreenshot('sidebar-not-found');
        
        // List what we found
        console.log('\n   🔍 Debug - Elements found:');
        for (const selector of planSelectors) {
          try {
            const elements = await this.driver.findElements(By.css(selector));
            if (elements.length > 0) {
              console.log(`   - ${selector}: ${elements.length} element(s)`);
              for (let i = 0; i < Math.min(2, elements.length); i++) {
                const text = await elements[i].getText();
                console.log(`     Preview: "${text.substring(0, 50)}..."`);
              }
            }
          } catch (e) {
            // Skip
          }
        }
      }
      
      if (tripPlanFound) {
        console.log('\n   📊 Trip Plan Analysis:');
        console.log('   ' + '─'.repeat(40));
        
        // Analyze content
        const analysis = {
          'Day-by-day itinerary': /day\s*\d/i.test(planContent),
          'Flight information': planContent.toLowerCase().includes('flight') || planContent.toLowerCase().includes('sfo'),
          'Hotel recommendations': planContent.toLowerCase().includes('hotel') || planContent.toLowerCase().includes('shibuya'),
          'Attractions mentioned': planContent.toLowerCase().includes('temple') || planContent.toLowerCase().includes('tower') || planContent.toLowerCase().includes('shrine'),
          'Restaurant suggestions': planContent.toLowerCase().includes('restaurant') || planContent.toLowerCase().includes('food') || planContent.toLowerCase().includes('sushi'),
          'Budget information': planContent.includes('$') || planContent.toLowerCase().includes('cost') || planContent.toLowerCase().includes('price')
        };
        
        Object.entries(analysis).forEach(([feature, found]) => {
          console.log(`   ${found ? '✅' : '❌'} ${feature}`);
        });
        
        // Extract sample content
        console.log('\n   📄 Content Sample:');
        console.log('   ' + '─'.repeat(40));
        
        // Try to extract Day 1
        const day1Match = planContent.match(/day\s*1[:\s-]*([\s\S]{0,200})/i);
        if (day1Match) {
          console.log(`   Day 1: ${day1Match[1].trim().substring(0, 100)}...`);
        }
        
        // Try to extract flight info
        const flightMatch = planContent.match(/flight[:\s]*([\s\S]{0,100})/i);
        if (flightMatch) {
          console.log(`   Flights: ${flightMatch[1].trim().substring(0, 100)}...`);
        }
        
        await this.takeScreenshot('05-trip-plan-displayed');
        
        console.log('\n   ✅ Trip plan successfully created and displayed!');
        return true;
        
      } else {
        throw new Error('Trip plan NOT found in the sidebar panel! The trip plan must appear in the right sidebar, not just in chat messages.');
      }
      
    } catch (error) {
      console.error('   ❌ Trip plan verification failed:', error.message);
      await this.takeScreenshot('trip-plan-error');
      throw error;
    }
  }

  async runTest() {
    console.log('\n🚀 Trip Plan Creation UI Test');
    console.log('═'.repeat(60));
    console.log(`📍 Target: ${this.baseUrl}`);
    console.log(`🕐 Started: ${new Date().toLocaleString()}`);
    console.log(`📁 Screenshots: ${this.screenshotDir}`);
    console.log('═'.repeat(60));
    
    try {
      await this.setup();
      
      // Run all test steps
      await this.login();
      await this.navigateToChat();
      await this.sendTravelRequest();
      await this.waitForAIResponse();
      await this.verifyTripPlan();
      
      // Success summary
      console.log('\n✅ TEST PASSED - All Steps Completed Successfully!');
      console.log('═'.repeat(60));
      console.log('📊 Summary:');
      console.log('   ✅ User authentication successful');
      console.log('   ✅ Navigation to chat page working');
      console.log('   ✅ Travel request sent to AI agent');
      console.log('   ✅ AI generated comprehensive travel plan');
      console.log('   ✅ Trip plan displayed in UI');
      console.log('═'.repeat(60));
      
      await this.takeScreenshot('06-test-success');
      
    } catch (error) {
      console.error('\n❌ TEST FAILED');
      console.error('═'.repeat(60));
      console.error('Error:', error.message);
      console.error('Stack:', error.stack);
      
      await this.takeScreenshot('test-failure');
      
    } finally {
      console.log(`\n🏁 Test completed: ${new Date().toLocaleString()}`);
      console.log(`📸 Screenshots saved to: ${this.screenshotDir}`);
      
      await this.cleanup();
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new TripPlanCreationTest();
  test.runTest().catch(console.error);
}

module.exports = TripPlanCreationTest;