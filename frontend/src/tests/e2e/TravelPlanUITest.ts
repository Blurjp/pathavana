import { Builder, By, until, WebDriver, WebElement } from 'selenium-webdriver';
import chrome from 'selenium-webdriver/chrome';

interface TestResult {
  testName: string;
  status: 'PASS' | 'FAIL';
  duration: number;
  error?: string;
  details?: any;
}

class TravelPlanUITest {
  private driver: WebDriver;
  private baseUrl: string;
  private results: TestResult[] = [];

  constructor(baseUrl: string = 'http://localhost:3000') {
    this.baseUrl = baseUrl;
    this.driver = this.createDriver();
  }

  private createDriver(): WebDriver {
    const options = new chrome.Options();
    options.addArguments('--disable-dev-shm-usage');
    options.addArguments('--no-sandbox');
    options.addArguments('--window-size=1920,1080');
    
    return new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
  }

  private async login(email: string = 'test@example.com', password: string = 'testpassword'): Promise<void> {
    console.log('🔐 Logging in...');
    
    // Click Sign In button in header
    const signInButton = await this.driver.findElement(By.xpath("//button[text()='Sign In']"));
    await signInButton.click();
    
    // Wait for login modal
    await this.driver.wait(until.elementLocated(By.css('[data-testid="login-modal"], .login-modal, .modal-content')), 10000);
    
    // Fill in login form
    const emailInput = await this.driver.findElement(By.css('input[type="email"], input[name="email"], input[placeholder*="email" i]'));
    await emailInput.clear();
    await emailInput.sendKeys(email);
    
    const passwordInput = await this.driver.findElement(By.css('input[type="password"], input[name="password"]'));
    await passwordInput.clear();
    await passwordInput.sendKeys(password);
    
    // Submit login form
    const submitButton = await this.driver.findElement(By.xpath("//button[contains(text(),'Sign in') or contains(text(),'Sign In') or contains(text(),'Login')]"));
    await submitButton.click();
    
    // Wait for authentication to complete - check for user avatar
    await this.driver.wait(until.elementLocated(By.css('.user-avatar, .avatar-placeholder')), 15000);
    console.log('✅ Login successful');
  }

  private async createNewChat(): Promise<void> {
    console.log('💬 Creating new chat...');
    
    // Navigate to chat page if not already there
    const currentUrl = await this.driver.getCurrentUrl();
    if (!currentUrl.includes('/chat')) {
      await this.driver.get(`${this.baseUrl}/chat`);
      await this.driver.wait(until.urlContains('/chat'), 10000);
    }
    
    // Look for new chat button or similar
    try {
      // Try to find a "New Chat" button
      const newChatButton = await this.driver.findElement(
        By.xpath("//button[contains(text(),'New Chat') or contains(text(),'new chat') or contains(@aria-label,'new chat')]")
      );
      await newChatButton.click();
      await this.driver.sleep(1000);
    } catch (e) {
      // If no new chat button, we might already be in a new chat
      console.log('📝 No explicit new chat button found, proceeding with current chat');
    }
    
    console.log('✅ Ready to send message');
  }

  private async sendChatMessage(message: string): Promise<void> {
    console.log(`📤 Sending message: "${message}"`);
    
    // Find chat input - try multiple selectors
    const chatInputSelectors = [
      'textarea[placeholder*="Type your message"]',
      'textarea[placeholder*="Ask me about"]',
      'input[placeholder*="Type your message"]',
      '.chat-input textarea',
      '.chat-input input',
      '[data-testid="chat-input"]',
      'textarea',
      'input[type="text"]'
    ];
    
    let chatInput: WebElement | null = null;
    for (const selector of chatInputSelectors) {
      try {
        chatInput = await this.driver.findElement(By.css(selector));
        const isDisplayed = await chatInput.isDisplayed();
        const isEnabled = await chatInput.isEnabled();
        if (isDisplayed && isEnabled) {
          break;
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    
    if (!chatInput) {
      throw new Error('Could not find chat input field');
    }
    
    await chatInput.clear();
    await chatInput.sendKeys(message);
    
    // Find and click send button - try multiple methods
    const sendButtonSelectors = [
      'button[type="submit"]',
      'button[aria-label*="send" i]',
      '.chat-input button',
      'button svg[data-icon="send"]',
      'button:has(svg)'
    ];
    
    let sendButton: WebElement | null = null;
    for (const selector of sendButtonSelectors) {
      try {
        const buttons = await this.driver.findElements(By.css(selector));
        for (const button of buttons) {
          const parent = await button.findElement(By.xpath('..'));
          const className = await parent.getAttribute('class');
          if (className && className.includes('chat-input')) {
            sendButton = button;
            break;
          }
        }
        if (sendButton) break;
      } catch (e) {
        // Continue
      }
    }
    
    if (!sendButton) {
      // Try Enter key as fallback
      await chatInput.sendKeys('\n');
    } else {
      await sendButton.click();
    }
    
    console.log('✅ Message sent');
  }

  private async waitForAIResponse(timeout: number = 30000): Promise<void> {
    console.log('⏳ Waiting for AI response...');
    
    const startTime = Date.now();
    
    // Wait for response to appear
    await this.driver.wait(async () => {
      // Check for various indicators of AI response
      const responseSelectors = [
        '.chat-message.assistant',
        '.message-assistant',
        '[data-role="assistant"]',
        '.ai-message',
        '.bot-message'
      ];
      
      for (const selector of responseSelectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          if (elements.length > 0) {
            // Check if the last message is not still loading
            const lastMessage = elements[elements.length - 1];
            const text = await lastMessage.getText();
            if (text && text.length > 10 && !text.includes('...')) {
              return true;
            }
          }
        } catch (e) {
          // Continue
        }
      }
      
      return false;
    }, timeout);
    
    const duration = Date.now() - startTime;
    console.log(`✅ AI response received in ${duration}ms`);
  }

  private async checkTravelPlanPanel(): Promise<boolean> {
    console.log('🔍 Checking for travel plan panel...');
    
    try {
      // Check if sidebar/panel is visible
      const panelSelectors = [
        '.trip-plan-panel',
        '.travel-plan-panel',
        '.sidebar-content',
        '[data-testid="trip-plan"]',
        '.search-results-sidebar'
      ];
      
      for (const selector of panelSelectors) {
        try {
          const panel = await this.driver.findElement(By.css(selector));
          const isDisplayed = await panel.isDisplayed();
          if (isDisplayed) {
            console.log(`✅ Found travel plan panel with selector: ${selector}`);
            
            // Check for content in the panel
            const panelText = await panel.getText();
            console.log(`📋 Panel content preview: ${panelText.substring(0, 200)}...`);
            
            // Look for travel-related content
            const travelKeywords = ['flight', 'hotel', 'itinerary', 'day', 'travel', 'trip', 'destination'];
            const hasTravel = travelKeywords.some(keyword => 
              panelText.toLowerCase().includes(keyword)
            );
            
            if (hasTravel) {
              console.log('✅ Travel plan content detected in panel');
              return true;
            }
          }
        } catch (e) {
          // Continue to next selector
        }
      }
      
      // If no dedicated panel, check if content appears in the main chat
      console.log('⚠️ No dedicated travel plan panel found, checking main chat area...');
      const chatMessages = await this.driver.findElements(By.css('.chat-message, .message'));
      for (const message of chatMessages) {
        const text = await message.getText();
        if (text.toLowerCase().includes('itinerary') || text.toLowerCase().includes('day 1')) {
          console.log('✅ Travel plan found in chat messages');
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('Error checking travel plan panel:', error);
      return false;
    }
  }

  private async captureScreenshot(name: string): Promise<void> {
    try {
      const screenshot = await this.driver.takeScreenshot();
      const fs = require('fs');
      const filename = `test-screenshots/${name}-${Date.now()}.png`;
      fs.mkdirSync('test-screenshots', { recursive: true });
      fs.writeFileSync(filename, screenshot, 'base64');
      console.log(`📸 Screenshot saved: ${filename}`);
    } catch (e) {
      console.error('Failed to capture screenshot:', e);
    }
  }

  private async runTest(testName: string, testFn: () => Promise<void>): Promise<void> {
    const startTime = Date.now();
    try {
      await testFn();
      this.results.push({
        testName,
        status: 'PASS',
        duration: Date.now() - startTime
      });
    } catch (error) {
      await this.captureScreenshot(`${testName}-error`);
      this.results.push({
        testName,
        status: 'FAIL',
        duration: Date.now() - startTime,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  public async runFullTest(): Promise<void> {
    console.log('🚀 Starting Travel Plan UI Test');
    console.log('================================\n');
    
    try {
      // Test 1: Navigate to homepage
      await this.runTest('Navigate to Homepage', async () => {
        await this.driver.get(this.baseUrl);
        await this.driver.wait(until.titleContains('Pathavana'), 10000);
        console.log('✅ Homepage loaded');
      });
      
      // Test 2: Login
      await this.runTest('User Login', async () => {
        await this.login();
      });
      
      // Test 3: Navigate to chat and create new chat
      await this.runTest('Create New Chat', async () => {
        await this.createNewChat();
      });
      
      // Test 4: Send travel planning message
      await this.runTest('Send Travel Planning Request', async () => {
        const travelRequest = "Create a 5-day travel plan to Paris, France. Include flights from New York, hotel recommendations, and daily itinerary with must-see attractions.";
        await this.sendChatMessage(travelRequest);
      });
      
      // Test 5: Wait for AI response
      await this.runTest('Wait for AI Response', async () => {
        await this.waitForAIResponse(60000); // 60 second timeout for complex request
      });
      
      // Test 6: Verify travel plan appears
      await this.runTest('Verify Travel Plan Display', async () => {
        // Give some time for the panel to render
        await this.driver.sleep(3000);
        
        const hasTravelPlan = await this.checkTravelPlanPanel();
        if (!hasTravelPlan) {
          throw new Error('Travel plan panel not found or does not contain travel content');
        }
        
        await this.captureScreenshot('travel-plan-success');
      });
      
      // Test 7: Interact with travel plan (optional)
      await this.runTest('Interact with Travel Plan', async () => {
        try {
          // Try to find and click on a flight or hotel card
          const interactiveElements = [
            '.flight-card',
            '.hotel-card',
            '.activity-card',
            '.trip-day',
            '[data-testid="travel-item"]'
          ];
          
          for (const selector of interactiveElements) {
            try {
              const element = await this.driver.findElement(By.css(selector));
              if (await element.isDisplayed()) {
                await element.click();
                console.log(`✅ Clicked on ${selector}`);
                await this.driver.sleep(1000);
                break;
              }
            } catch (e) {
              // Continue
            }
          }
        } catch (e) {
          console.log('ℹ️ No interactive elements found in travel plan (optional test)');
        }
      });
      
    } finally {
      // Print test results
      console.log('\n================================');
      console.log('📊 Test Results Summary');
      console.log('================================\n');
      
      let passed = 0;
      let failed = 0;
      
      for (const result of this.results) {
        const status = result.status === 'PASS' ? '✅' : '❌';
        console.log(`${status} ${result.testName} (${result.duration}ms)`);
        if (result.error) {
          console.log(`   Error: ${result.error}`);
        }
        
        if (result.status === 'PASS') passed++;
        else failed++;
      }
      
      console.log(`\nTotal: ${this.results.length} | Passed: ${passed} | Failed: ${failed}`);
      console.log(`Success Rate: ${((passed / this.results.length) * 100).toFixed(1)}%`);
      
      // Close browser
      await this.driver.quit();
    }
  }
}

// Run the test
if (require.main === module) {
  const test = new TravelPlanUITest();
  test.runFullTest().catch(console.error);
}

export default TravelPlanUITest;