const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test trip plan creation and sidebar display
 */
async function tripPlanSidebarTest() {
  console.log('🗺️  Trip Plan Sidebar Test');
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
    
    // Wait for chat page
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully\n');
    
    await driver.sleep(2000);
    
    // Test 1: Check initial sidebar state
    console.log('📝 Test 1: Initial Sidebar State');
    console.log('─'.repeat(40));
    
    // Check if sidebar exists
    const sidebarElements = await driver.findElements(By.css('[class*="sidebar"]'));
    console.log(`  Sidebar elements found: ${sidebarElements.length}`);
    
    // Check for trip plan section
    const tripPlanElements = await driver.findElements(By.css('[class*="trip-plan"], [class*="TripPlan"], [class*="selected-items"]'));
    console.log(`  Trip plan elements found: ${tripPlanElements.length}`);
    
    // Check sidebar visibility
    let sidebarVisible = false;
    for (const sidebar of sidebarElements) {
      const isDisplayed = await sidebar.isDisplayed();
      if (isDisplayed) {
        sidebarVisible = true;
        const rect = await sidebar.getRect();
        console.log(`  Sidebar visible: ${isDisplayed}, Width: ${rect.width}px`);
      }
    }
    
    // Test 2: Send message to trigger search
    console.log('\n📝 Test 2: Trigger Flight Search');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('Search for flights from San Francisco to Tokyo on March 15, 2024 for 2 adults');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for AI response and search...');
    await driver.sleep(10000);
    
    // Check if search results appear
    const searchResults = await driver.findElements(By.css('[class*="search-results"], [class*="SearchResults"], [class*="flight-option"], [class*="FlightOption"]'));
    console.log(`  Search result elements found: ${searchResults.length}`);
    
    // Check if sidebar opened automatically
    const sidebarAfterSearch = await driver.findElements(By.css('[class*="sidebar"][class*="open"], [class*="sidebar"][class*="visible"], [class*="sidebar"]:not([class*="closed"])'));
    console.log(`  Sidebar open after search: ${sidebarAfterSearch.length > 0}`);
    
    // Test 3: Add item to trip plan
    console.log('\n📝 Test 3: Add Flight to Trip Plan');
    console.log('─'.repeat(40));
    
    // Look for "Add to trip" or similar buttons
    const addButtons = await driver.findElements(By.css('button[class*="add"], button[class*="save"], button[class*="select"], [class*="add-to-trip"]'));
    console.log(`  Add buttons found: ${addButtons.length}`);
    
    if (addButtons.length > 0) {
      // Click the first add button
      try {
        await addButtons[0].click();
        console.log('  ✅ Clicked add button');
        await driver.sleep(2000);
      } catch (e) {
        console.log('  ⚠️  Could not click add button:', e.message);
      }
    }
    
    // Test 4: Check trip plan in sidebar
    console.log('\n📝 Test 4: Check Trip Plan in Sidebar');
    console.log('─'.repeat(40));
    
    // Check for saved items
    const savedItems = await driver.findElements(By.css('[class*="saved-item"], [class*="selected-item"], [class*="trip-item"]'));
    console.log(`  Saved items found: ${savedItems.length}`);
    
    // Check for trip plan summary
    const tripSummary = await driver.findElements(By.css('[class*="trip-summary"], [class*="TripSummary"], [class*="itinerary"]'));
    console.log(`  Trip summary elements found: ${tripSummary.length}`);
    
    // Test 5: Interact with trip plan
    console.log('\n📝 Test 5: Trip Plan Interaction');
    console.log('─'.repeat(40));
    
    // Try to find trip plan toggle or tab
    const tripPlanToggles = await driver.findElements(By.css('[class*="trip-plan-toggle"], [class*="view-trip"], button[class*="trip"]'));
    console.log(`  Trip plan toggles found: ${tripPlanToggles.length}`);
    
    if (tripPlanToggles.length > 0) {
      try {
        await tripPlanToggles[0].click();
        console.log('  ✅ Clicked trip plan toggle');
        await driver.sleep(2000);
      } catch (e) {
        console.log('  ⚠️  Could not click trip plan toggle:', e.message);
      }
    }
    
    // Test 6: Search for hotels
    console.log('\n📝 Test 6: Add Hotel to Trip Plan');
    console.log('─'.repeat(40));
    
    await chatInput.clear();
    await chatInput.sendKeys('Find hotels in Tokyo Shibuya area for March 15-20');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for hotel results...');
    await driver.sleep(8000);
    
    // Check for hotel results
    const hotelResults = await driver.findElements(By.css('[class*="hotel-option"], [class*="HotelOption"], [class*="hotel-result"]'));
    console.log(`  Hotel result elements found: ${hotelResults.length}`);
    
    // Final check of trip plan
    console.log('\n📝 Final Trip Plan Status');
    console.log('─'.repeat(40));
    
    // Get all trip plan related elements
    const finalTripElements = await driver.executeScript(`
      const elements = {
        sidebar: document.querySelectorAll('[class*="sidebar"]').length,
        searchResults: document.querySelectorAll('[class*="search-results"]').length,
        savedItems: document.querySelectorAll('[class*="saved-item"], [class*="selected-item"]').length,
        tripPlan: document.querySelectorAll('[class*="trip-plan"], [class*="TripPlan"]').length,
        flights: document.querySelectorAll('[class*="flight"]').length,
        hotels: document.querySelectorAll('[class*="hotel"]').length
      };
      
      // Check sidebar visibility
      const sidebar = document.querySelector('[class*="sidebar"]');
      if (sidebar) {
        const styles = window.getComputedStyle(sidebar);
        elements.sidebarVisible = styles.display !== 'none' && styles.visibility !== 'hidden';
        elements.sidebarWidth = sidebar.offsetWidth;
      }
      
      return elements;
    `);
    
    console.log('  Element counts:', finalTripElements);
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Sidebar exists: ${finalTripElements.sidebar > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Search results display: ${finalTripElements.searchResults > 0 || finalTripElements.flights > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip plan section exists: ${finalTripElements.tripPlan > 0 || finalTripElements.savedItems > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Sidebar is visible: ${finalTripElements.sidebarVisible ? 'PASS' : 'FAIL'}`);
    
    // Take screenshot for analysis
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-sidebar-test.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as trip-plan-sidebar-test.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Take error screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-sidebar-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as trip-plan-sidebar-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
tripPlanSidebarTest().catch(console.error);