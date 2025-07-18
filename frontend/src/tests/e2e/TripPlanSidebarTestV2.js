const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Enhanced test for trip plan creation and sidebar display
 */
async function tripPlanSidebarTestV2() {
  console.log('🗺️  Trip Plan Sidebar Test V2');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  const elementCounts = {};
  
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
    
    // Check sidebar state
    console.log('📝 Test 1: Initial Sidebar State');
    console.log('─'.repeat(40));
    
    const sidebarElements = await driver.findElements(By.css('.search-results-sidebar, .sidebar'));
    const tripPlanElements = await driver.findElements(By.css('.trip-plan, .trip-plan-panel'));
    const tripPlanTabElements = await driver.findElements(By.xpath("//button[contains(text(), 'Trip Plan')]"));
    
    elementCounts.sidebar = sidebarElements.length;
    elementCounts.tripPlan = tripPlanElements.length;
    
    console.log(`  Sidebar elements found: ${sidebarElements.length}`);
    console.log(`  Trip plan elements found: ${tripPlanElements.length}`);
    console.log(`  Trip plan tab found: ${tripPlanTabElements.length}`);
    
    // Check if sidebar is visible
    let sidebarVisible = false;
    if (sidebarElements.length > 0) {
      sidebarVisible = await sidebarElements[0].isDisplayed();
      const sidebarWidth = await sidebarElements[0].getCssValue('width');
      console.log(`  Sidebar visible: ${sidebarVisible}, Width: ${sidebarWidth}`);
      elementCounts.sidebarVisible = sidebarVisible;
      elementCounts.sidebarWidth = parseInt(sidebarWidth) || 0;
    }
    
    // Trigger search
    console.log('\n📝 Test 2: Trigger Flight Search');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea[placeholder*="Continue planning"]')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo on March 15, 2024');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for AI response and search...');
    await driver.sleep(10000);
    
    // Check for search results in sidebar
    const searchResultElements = await driver.findElements(
      By.css('.search-results-sidebar .flights-list, .search-results-sidebar .flight-card')
    );
    elementCounts.searchResults = searchResultElements.length;
    console.log(`  Search result elements found: ${searchResultElements.length}`);
    
    // Check if sidebar opened
    const openSidebar = await driver.findElements(By.css('.search-results-sidebar'));
    const sidebarOpen = openSidebar.length > 0 && await openSidebar[0].isDisplayed();
    console.log(`  Sidebar open after search: ${sidebarOpen}`);
    
    // Add flight to trip
    console.log('\n📝 Test 3: Add Flight to Trip Plan');
    console.log('─'.repeat(40));
    
    // Look for Add to Trip buttons in FlightCard components
    const addToTripButtons = await driver.findElements(
      By.css('.flight-card .add-to-trip, .flight-card button[title="Add to trip"]')
    );
    elementCounts.addButtons = addToTripButtons.length;
    console.log(`  Add to Trip buttons found: ${addToTripButtons.length}`);
    
    if (addToTripButtons.length > 0) {
      try {
        // Scroll to the button and click it
        await driver.executeScript("arguments[0].scrollIntoView(true);", addToTripButtons[0]);
        await driver.sleep(500);
        await addToTripButtons[0].click();
        console.log('  ✅ Clicked Add to Trip button');
        await driver.sleep(2000);
      } catch (e) {
        console.log('  ❌ Could not click Add to Trip button:', e.message);
      }
    }
    
    // Click Trip Plan tab
    console.log('\n📝 Test 4: Click Trip Plan Tab');
    console.log('─'.repeat(40));
    
    // Click on Trip Plan tab
    try {
      const tripPlanTab = await driver.findElement(By.xpath("//button[contains(text(), 'Trip Plan')]"));
      await driver.executeScript("arguments[0].scrollIntoView(true);", tripPlanTab);
      await tripPlanTab.click();
      console.log('  ✅ Clicked Trip Plan tab');
      await driver.sleep(2000);
    } catch (e) {
      console.log('  ❌ Could not find/click Trip Plan tab:', e.message);
    }
    
    // Check if trip plan section shows added items
    const savedItems = await driver.findElements(
      By.css('.trip-plan-item, .itinerary-item, .trip-item')
    );
    elementCounts.savedItems = savedItems.length;
    console.log(`  Saved items found: ${savedItems.length}`);
    
    // Look for trip summary
    const tripSummary = await driver.findElements(
      By.css('.trip-summary, .trip-overview, .itinerary-summary')
    );
    console.log(`  Trip summary elements found: ${tripSummary.length}`);
    
    // Check TripPlanPanel specifically
    console.log('\n📝 Test 5: Check TripPlanPanel Component');
    console.log('─'.repeat(40));
    
    const tripPlanPanel = await driver.findElements(By.css('.trip-plan-panel'));
    console.log(`  TripPlanPanel found: ${tripPlanPanel.length}`);
    
    if (tripPlanPanel.length > 0) {
      const isPanelVisible = await tripPlanPanel[0].isDisplayed();
      console.log(`  TripPlanPanel visible: ${isPanelVisible}`);
      
      // Check for itinerary items inside TripPlanPanel
      const itineraryItems = await driver.findElements(
        By.css('.trip-plan-panel .itinerary-day, .trip-plan-panel .itinerary-item')
      );
      console.log(`  Itinerary items in panel: ${itineraryItems.length}`);
    }
    
    // Search for hotels
    console.log('\n📝 Test 6: Add Hotel to Trip Plan');
    console.log('─'.repeat(40));
    
    // Go back to flights tab first
    try {
      const flightsTab = await driver.findElement(By.xpath("//button[contains(text(), 'Flights')]"));
      await flightsTab.click();
      await driver.sleep(1000);
    } catch (e) {
      console.log('  Could not switch to flights tab');
    }
    
    await chatInput.clear();
    await chatInput.sendKeys('Find hotels in Tokyo Shibuya area for March 15-20');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for hotel results...');
    await driver.sleep(8000);
    
    // Click Hotels tab
    try {
      const hotelsTab = await driver.findElement(By.xpath("//button[contains(text(), 'Hotels')]"));
      await hotelsTab.click();
      await driver.sleep(1000);
    } catch (e) {
      console.log('  Could not switch to hotels tab');
    }
    
    const hotelResults = await driver.findElements(
      By.css('.search-results-sidebar .hotels-list, .search-results-sidebar .hotel-card')
    );
    elementCounts.hotels = hotelResults.length;
    console.log(`  Hotel result elements found: ${hotelResults.length}`);
    
    // Final verification
    console.log('\n📝 Final Trip Plan Status');
    console.log('─'.repeat(40));
    
    // Get comprehensive element count
    const finalCounts = await driver.executeScript(`
      const sidebar = document.querySelector('.search-results-sidebar');
      const results = {
        sidebarExists: !!sidebar,
        sidebarVisible: sidebar ? window.getComputedStyle(sidebar).display !== 'none' : false,
        sidebarWidth: sidebar ? sidebar.offsetWidth : 0,
        tripPlanTab: document.querySelectorAll('button:contains("Trip Plan")').length || 
                     Array.from(document.querySelectorAll('button')).filter(b => b.textContent.includes('Trip Plan')).length,
        flightCards: document.querySelectorAll('.flight-card').length,
        hotelCards: document.querySelectorAll('.hotel-card').length,
        addToTripButtons: document.querySelectorAll('.add-to-trip, button[title="Add to trip"]').length,
        tripPlanPanel: document.querySelectorAll('.trip-plan-panel').length,
        itineraryItems: document.querySelectorAll('.itinerary-item').length
      };
      
      // Debug: log all buttons in sidebar
      const sidebarButtons = sidebar ? Array.from(sidebar.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
      results.sidebarButtons = sidebarButtons;
      
      return results;
    `);
    
    console.log('  Final element counts:', JSON.stringify(finalCounts, null, 2));
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Sidebar exists: ${finalCounts.sidebarExists ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Search results display: ${finalCounts.flightCards > 0 || finalCounts.hotelCards > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip Plan tab exists: ${finalCounts.tripPlanTab > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Add to Trip buttons: ${finalCounts.addToTripButtons > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip plan functionality: ${finalCounts.tripPlanPanel > 0 || finalCounts.itineraryItems > 0 ? 'PASS' : 'FAIL'}`);
    
    // Take screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-sidebar-test-v2.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as trip-plan-sidebar-test-v2.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-sidebar-error-v2.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as trip-plan-sidebar-error-v2.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
tripPlanSidebarTestV2().catch(console.error);