const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test flight and hotel search with mock data integration
 */
async function testWithMockData() {
  console.log('🧪 Test With Mock Data Integration');
  console.log('═'.repeat(60));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  try {
    // Navigate and login
    await driver.get('http://localhost:3000');
    await driver.sleep(2000);
    
    await driver.executeScript(`
      localStorage.clear();
      sessionStorage.clear();
    `);
    
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
    
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully\n');
    
    await driver.sleep(2000);
    
    // Test 1: Search for flights
    console.log('📝 Test 1: Search for Flights');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for response and mock data...');
    await driver.sleep(10000);
    
    // Check if flight cards appear
    const flightCheck = await driver.executeScript(`
      return {
        sidebarOpen: document.querySelector('.search-results-sidebar')?.offsetWidth > 100,
        flightCards: document.querySelectorAll('.flight-card').length,
        loadingState: !!document.querySelector('.loading-state'),
        emptyState: !!document.querySelector('.empty-state'),
        addButtons: document.querySelectorAll('.add-to-trip').length
      };
    `);
    
    console.log('  Flight search results:', JSON.stringify(flightCheck, null, 2));
    
    // Test 2: Click Add to Trip if available
    console.log('\n📝 Test 2: Add Flight to Trip');
    console.log('─'.repeat(40));
    
    if (flightCheck.addButtons > 0) {
      await driver.executeScript(`
        const addButton = document.querySelector('.add-to-trip');
        if (addButton) {
          addButton.scrollIntoView();
          addButton.click();
        }
      `);
      
      console.log('  ✅ Clicked Add to Trip button');
      await driver.sleep(2000);
    } else {
      console.log('  ⚠️  No Add to Trip buttons found');
    }
    
    // Test 3: Check Trip Plan
    console.log('\n📝 Test 3: Check Trip Plan');
    console.log('─'.repeat(40));
    
    // Click Trip Plan tab
    await driver.executeScript(`
      const tripPlanTab = Array.from(document.querySelectorAll('.sidebar-tabs button'))
        .find(btn => btn.textContent.includes('Trip Plan'));
      if (tripPlanTab) tripPlanTab.click();
    `);
    
    await driver.sleep(1000);
    
    const tripPlanCheck = await driver.executeScript(`
      const panel = document.querySelector('.trip-plan-panel');
      const items = document.querySelectorAll('.itinerary-item');
      
      return {
        panelExists: !!panel,
        itemCount: items.length,
        hasEmptyState: panel ? panel.textContent.includes('No trip plan yet') : true,
        panelContent: panel ? panel.textContent.substring(0, 100) : 'not found'
      };
    `);
    
    console.log('  Trip Plan state:', JSON.stringify(tripPlanCheck, null, 2));
    
    // Test 4: Search for hotels
    console.log('\n📝 Test 4: Search for Hotels');
    console.log('─'.repeat(40));
    
    // Go back to Flights tab
    await driver.executeScript(`
      const flightsTab = document.querySelector('.sidebar-tabs button');
      if (flightsTab) flightsTab.click();
    `);
    
    await chatInput.clear();
    await chatInput.sendKeys('Find hotels in Tokyo');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for hotel results...');
    await driver.sleep(10000);
    
    // Click Hotels tab
    await driver.executeScript(`
      const hotelsTab = Array.from(document.querySelectorAll('.sidebar-tabs button'))
        .find(btn => btn.textContent.includes('Hotels'));
      if (hotelsTab) hotelsTab.click();
    `);
    
    await driver.sleep(1000);
    
    const hotelCheck = await driver.executeScript(`
      return {
        hotelCards: document.querySelectorAll('.hotel-card').length,
        addButtons: document.querySelectorAll('.hotel-card .add-to-trip, .add-to-trip-button').length,
        activeTab: document.querySelector('.sidebar-tabs button.active')?.textContent
      };
    `);
    
    console.log('  Hotel search results:', JSON.stringify(hotelCheck, null, 2));
    
    // Take final screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('test-with-mock-data.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as test-with-mock-data.png');
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Sidebar opens: ${flightCheck.sidebarOpen ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Flight cards display: ${flightCheck.flightCards > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Hotel cards display: ${hotelCheck.hotelCards > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Add to Trip buttons: ${flightCheck.addButtons > 0 || hotelCheck.addButtons > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip Plan panel: ${tripPlanCheck.panelExists ? 'PASS' : 'FAIL'}`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('test-mock-data-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as test-mock-data-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
testWithMockData().catch(console.error);