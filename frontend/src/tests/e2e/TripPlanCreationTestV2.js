const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs').promises;
const path = require('path');

/**
 * Trip Plan Creation Test V2
 * This test properly verifies that the trip plan appears in the sidebar
 * by following the actual user flow:
 * 1. Send travel request to AI
 * 2. Wait for search results to appear
 * 3. Add items (flights/hotels) to the trip
 * 4. Click the "Trip Plan" tab in sidebar
 * 5. Verify trip plan is displayed
 */
class TripPlanCreationTestV2 {
  constructor() {
    this.driver = null;
    this.baseUrl = 'http://localhost:3000';
    this.screenshotDir = null;
    this.screenshotCount = 0;
  }

  async setup() {
    // Create screenshots directory
    const timestamp = Date.now();
    this.screenshotDir = path.join(__dirname, 'screenshots', `test-run-${timestamp}`);
    await fs.mkdir(this.screenshotDir, { recursive: true });
    
    // Setup Chrome options
    const options = new chrome.Options();
    options.addArguments('--window-size=1920,1080');
    options.addArguments('--disable-dev-shm-usage');
    
    // Create driver
    this.driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(options)
      .build();
    
    console.log('✅ Chrome WebDriver ready');
  }

  async takeScreenshot(name) {
    try {
      const screenshot = await this.driver.takeScreenshot();
      const filename = `${String(this.screenshotCount++).padStart(2, '0')}-${name}.png`;
      const filepath = path.join(this.screenshotDir, filename);
      await fs.writeFile(filepath, screenshot, 'base64');
      console.log(`   📸 Screenshot: ${filepath}`);
    } catch (error) {
      console.error(`   ⚠️  Failed to take screenshot: ${error.message}`);
    }
  }

  async login() {
    console.log('\n🔐 Step 1: User Authentication');
    console.log('━'.repeat(50));
    
    try {
      // Navigate to homepage
      console.log('   📍 Navigating to homepage...');
      await this.driver.get(this.baseUrl);
      await this.driver.wait(until.titleContains('Pathavana'), 10000);
      
      // Click Sign In
      const signInButton = await this.driver.wait(
        until.elementLocated(By.css('.auth-buttons button:first-child')),
        10000
      );
      await signInButton.click();
      console.log('   ✅ Clicked Sign In button');
      
      // Fill login form
      await this.driver.sleep(1000);
      const emailInput = await this.driver.findElement(By.css('input[type="email"]'));
      await emailInput.sendKeys('selenium.test@example.com');
      
      const passwordInput = await this.driver.findElement(By.css('input[type="password"]'));
      await passwordInput.sendKeys('SeleniumTest123!');
      
      const submitButton = await this.driver.findElement(By.css('button[type="submit"]'));
      await submitButton.click();
      console.log('   ✅ Submitted login form');
      
      // Wait for authentication
      await this.driver.wait(until.urlContains('/chat'), 15000);
      await this.driver.sleep(2000);
      
      console.log('   ✅ Authentication successful!');
      await this.takeScreenshot('logged-in');
      
    } catch (error) {
      console.error('   ❌ Login failed:', error.message);
      await this.takeScreenshot('login-error');
      throw error;
    }
  }

  async sendSearchRequest() {
    console.log('\n💬 Step 2: Send Search Request');
    console.log('━'.repeat(50));
    
    try {
      // Find chat input
      const chatInput = await this.driver.wait(
        until.elementLocated(By.css('textarea[placeholder*="travel"]')),
        10000
      );
      
      // Send a search request that will trigger searches
      const searchRequest = 'Search for flights from San Francisco to Tokyo next month under $800 and hotels in Shibuya';
      await chatInput.clear();
      await chatInput.sendKeys(searchRequest);
      console.log('   📝 Typed search request');
      
      // Send message
      await chatInput.sendKeys(Key.RETURN);
      console.log('   ✅ Sent search request');
      
      await this.takeScreenshot('search-request-sent');
      
    } catch (error) {
      console.error('   ❌ Failed to send search request:', error.message);
      await this.takeScreenshot('search-error');
      throw error;
    }
  }

  async waitForSearchResults() {
    console.log('\n🔍 Step 3: Wait for Search Results');
    console.log('━'.repeat(50));
    
    try {
      console.log('   ⏳ Waiting for search results to appear...');
      
      // Wait for search results in sidebar
      const timeout = 60000; // 60 seconds for search
      const startTime = Date.now();
      let resultsFound = false;
      
      while (Date.now() - startTime < timeout) {
        // Look for flight or hotel cards in sidebar
        const resultSelectors = [
          '.flight-card',
          '.hotel-card',
          '.search-result-card',
          '[class*="result-card"]',
          '.sidebar-content .card'
        ];
        
        for (const selector of resultSelectors) {
          try {
            const results = await this.driver.findElements(By.css(selector));
            if (results.length > 0) {
              resultsFound = true;
              console.log(`   ✅ Found ${results.length} search results`);
              break;
            }
          } catch (e) {
            continue;
          }
        }
        
        if (resultsFound) break;
        
        // Show progress
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (elapsed % 10 === 0 && elapsed > 0) {
          console.log(`   ⏱️  ${elapsed} seconds elapsed...`);
        }
        
        await this.driver.sleep(1000);
      }
      
      if (!resultsFound) {
        throw new Error('Timeout waiting for search results');
      }
      
      await this.takeScreenshot('search-results');
      return true;
      
    } catch (error) {
      console.error('   ❌ Search results error:', error.message);
      await this.takeScreenshot('search-results-error');
      throw error;
    }
  }

  async addItemsToTrip() {
    console.log('\n➕ Step 4: Add Items to Trip');
    console.log('━'.repeat(50));
    
    try {
      // Find "Add to trip" buttons
      const addButtonSelectors = [
        'button[title*="Add to trip"]',
        'button[aria-label*="Add to trip"]',
        '.add-to-trip-btn',
        'button .icon-plus',
        'button:has(.icon-plus)'
      ];
      
      let addedCount = 0;
      
      for (const selector of addButtonSelectors) {
        try {
          const buttons = await this.driver.findElements(By.css(selector));
          
          // Add first 2 items (flight and hotel)
          for (let i = 0; i < Math.min(2, buttons.length); i++) {
            if (await buttons[i].isDisplayed()) {
              await buttons[i].click();
              addedCount++;
              console.log(`   ✅ Added item ${addedCount} to trip`);
              await this.driver.sleep(1000);
              
              if (addedCount >= 2) break;
            }
          }
          
          if (addedCount >= 2) break;
        } catch (e) {
          continue;
        }
      }
      
      if (addedCount === 0) {
        // Try fallback: look for any plus icon
        const plusIcons = await this.driver.findElements(By.css('button'));
        for (const button of plusIcons) {
          const text = await button.getText();
          if (text.includes('➕') || text.includes('+')) {
            await button.click();
            addedCount++;
            console.log(`   ✅ Added item to trip (via plus icon)`);
            await this.driver.sleep(1000);
            if (addedCount >= 2) break;
          }
        }
      }
      
      if (addedCount === 0) {
        throw new Error('Could not find any "Add to trip" buttons');
      }
      
      console.log(`   ✅ Total items added to trip: ${addedCount}`);
      await this.takeScreenshot('items-added');
      
    } catch (error) {
      console.error('   ❌ Failed to add items to trip:', error.message);
      await this.takeScreenshot('add-items-error');
      throw error;
    }
  }

  async verifyTripPlanInSidebar() {
    console.log('\n📋 Step 5: Verify Trip Plan in Sidebar');
    console.log('━'.repeat(50));
    
    try {
      // Click the "Trip Plan" tab
      console.log('   🔍 Looking for Trip Plan tab...');
      
      const tabSelectors = [
        'button:contains("Trip Plan")',
        '.tab:contains("Trip Plan")',
        'button.tab:nth-child(3)', // Usually 3rd tab
        '[role="tab"]:contains("Trip Plan")'
      ];
      
      let tabClicked = false;
      
      // First try text-based search
      const allButtons = await this.driver.findElements(By.css('button'));
      for (const button of allButtons) {
        const text = await button.getText();
        if (text.includes('Trip Plan')) {
          await button.click();
          tabClicked = true;
          console.log('   ✅ Clicked Trip Plan tab');
          break;
        }
      }
      
      if (!tabClicked) {
        // Try by position (usually 3rd tab)
        const tabs = await this.driver.findElements(By.css('.tab, button.tab'));
        if (tabs.length >= 3) {
          await tabs[2].click(); // 0-indexed, so 3rd tab is index 2
          tabClicked = true;
          console.log('   ✅ Clicked 3rd tab (assumed to be Trip Plan)');
        }
      }
      
      if (!tabClicked) {
        throw new Error('Could not find Trip Plan tab');
      }
      
      await this.driver.sleep(2000); // Wait for tab content to load
      
      // Verify trip plan content is displayed
      console.log('   🔍 Verifying trip plan content...');
      
      const tripPlanSelectors = [
        '.trip-plan-panel',
        '.TripPlanPanel',
        '.plan-summary',
        '.plan-days',
        '.plan-day',
        '.trip-itinerary',
        '[class*="trip-plan"]'
      ];
      
      let tripPlanFound = false;
      let planContent = '';
      
      for (const selector of tripPlanSelectors) {
        try {
          const elements = await this.driver.findElements(By.css(selector));
          if (elements.length > 0) {
            const element = elements[0];
            if (await element.isDisplayed()) {
              planContent = await element.getText();
              if (planContent && planContent.length > 20) {
                tripPlanFound = true;
                console.log(`   ✅ Found trip plan in: ${selector}`);
                break;
              }
            }
          }
        } catch (e) {
          continue;
        }
      }
      
      if (!tripPlanFound) {
        // Debug: Get all visible text in sidebar
        try {
          const sidebar = await this.driver.findElement(By.css('[class*="sidebar"]'));
          const sidebarText = await sidebar.getText();
          console.log('   🔍 Sidebar content:', sidebarText.substring(0, 200) + '...');
        } catch (e) {
          console.log('   ⚠️  Could not read sidebar content');
        }
        
        throw new Error('Trip plan NOT found in sidebar! The trip plan must be visible in the Trip Plan tab.');
      }
      
      // Analyze trip plan content
      console.log('\n   📊 Trip Plan Content:');
      console.log('   ' + '─'.repeat(40));
      
      const hasItems = planContent.includes('Flight') || planContent.includes('Hotel') || 
                      planContent.includes('Day') || planContent.includes('$');
      const hasDestination = planContent.toLowerCase().includes('tokyo');
      const hasDates = /\d{4}|\w+ \d+|next month/i.test(planContent);
      
      console.log(`   ✅ Has saved items: ${hasItems}`);
      console.log(`   ✅ Shows destination: ${hasDestination}`);
      console.log(`   ✅ Shows dates: ${hasDates}`);
      
      console.log('\n   📄 Trip Plan Preview:');
      console.log('   ' + '─'.repeat(40));
      console.log(`   ${planContent.substring(0, 200)}...`);
      
      await this.takeScreenshot('trip-plan-displayed');
      
      console.log('\n   ✅ Trip plan successfully displayed in sidebar!');
      return true;
      
    } catch (error) {
      console.error('   ❌ Trip plan verification failed:', error.message);
      await this.takeScreenshot('trip-plan-error');
      throw error;
    }
  }

  async runTest() {
    console.log('\n🚀 Trip Plan Creation UI Test V2');
    console.log('════════════════════════════════════════════════════════════');
    console.log('📍 Target:', this.baseUrl);
    console.log('🕐 Started:', new Date().toLocaleString());
    console.log('📁 Screenshots:', this.screenshotDir);
    console.log('════════════════════════════════════════════════════════════');
    
    try {
      await this.setup();
      await this.login();
      await this.sendSearchRequest();
      await this.waitForSearchResults();
      await this.addItemsToTrip();
      await this.verifyTripPlanInSidebar();
      
      console.log('\n✅ TEST PASSED - Trip Plan Successfully Created and Displayed in Sidebar!');
      console.log('════════════════════════════════════════════════════════════');
      console.log('📊 Summary:');
      console.log('   ✅ User authentication successful');
      console.log('   ✅ Search request processed');
      console.log('   ✅ Search results displayed');
      console.log('   ✅ Items added to trip');
      console.log('   ✅ Trip Plan tab clicked');
      console.log('   ✅ Trip plan visible in sidebar');
      console.log('════════════════════════════════════════════════════════════');
      
      await this.takeScreenshot('test-success');
      
    } catch (error) {
      console.log('\n❌ TEST FAILED');
      console.log('════════════════════════════════════════════════════════════');
      console.log('Error:', error.message);
      console.log('Stack:', error.stack);
      
      await this.takeScreenshot('test-failure');
      process.exit(1);
      
    } finally {
      console.log('\n🏁 Test completed:', new Date().toLocaleString());
      console.log('📸 Screenshots saved to:', this.screenshotDir);
      
      if (this.driver) {
        await this.driver.sleep(2000); // Keep browser open briefly
        await this.driver.quit();
        console.log('🧹 Browser closed');
      }
    }
  }
}

// Run the test
const test = new TripPlanCreationTestV2();
test.runTest().catch(console.error);