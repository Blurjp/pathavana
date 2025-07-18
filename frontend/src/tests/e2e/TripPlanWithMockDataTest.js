const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test trip plan functionality with mock data
 */
async function tripPlanWithMockDataTest() {
  console.log('🗺️  Trip Plan Test with Mock Data');
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
    
    // Inject mock data directly into React state
    console.log('💉 Injecting mock flight data...');
    await driver.executeScript(`
      // Create mock flight data
      const mockFlights = [
        {
          id: 'mock-flight-1',
          airline: 'United Airlines',
          flightNumber: 'UA890',
          origin: {
            code: 'SFO',
            city: 'San Francisco',
            airport: 'San Francisco International'
          },
          destination: {
            code: 'NRT',
            city: 'Tokyo',
            airport: 'Narita International'
          },
          departureTime: '2024-03-15T08:00:00Z',
          arrivalTime: '2024-03-16T14:30:00Z',
          duration: '10h 30m',
          price: {
            amount: 850,
            currency: 'USD',
            displayPrice: '$850'
          },
          stops: 0,
          amenities: ['WiFi', 'Entertainment', 'Meals'],
          aircraft: 'Boeing 787-9'
        },
        {
          id: 'mock-flight-2',
          airline: 'ANA',
          flightNumber: 'NH7',
          origin: {
            code: 'SFO',
            city: 'San Francisco',
            airport: 'San Francisco International'
          },
          destination: {
            code: 'HND',
            city: 'Tokyo',
            airport: 'Haneda Airport'
          },
          departureTime: '2024-03-15T11:00:00Z',
          arrivalTime: '2024-03-16T16:20:00Z',
          duration: '11h 20m',
          price: {
            amount: 920,
            currency: 'USD',
            displayPrice: '$920'
          },
          stops: 0,
          amenities: ['WiFi', 'Premium Meals', 'Entertainment'],
          aircraft: 'Boeing 777-300ER'
        }
      ];
      
      // Try to directly update React state if possible
      const chatContainer = document.querySelector('.chat-container');
      if (chatContainer && chatContainer._reactInternalFiber) {
        console.log('Found React fiber');
      }
      
      // Dispatch a custom event with mock data
      window.dispatchEvent(new CustomEvent('mockSearchResults', {
        detail: {
          flights: mockFlights,
          hotels: [],
          activities: []
        }
      }));
      
      console.log('Mock data injected');
    `);
    
    await driver.sleep(2000);
    
    // Send a message to trigger the UI
    console.log('\n📝 Sending flight search message...');
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo on March 15');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('⏳ Waiting for response...');
    await driver.sleep(8000);
    
    // Check sidebar state
    console.log('\n📝 Checking Sidebar State');
    console.log('─'.repeat(40));
    
    const sidebarState = await driver.executeScript(`
      const sidebar = document.querySelector('.search-results-sidebar');
      const results = {
        sidebarExists: !!sidebar,
        sidebarVisible: sidebar ? window.getComputedStyle(sidebar).display !== 'none' : false,
        sidebarWidth: sidebar ? sidebar.offsetWidth : 0
      };
      
      // Check for tabs
      const tabs = Array.from(document.querySelectorAll('.sidebar-tabs button')).map(b => b.textContent.trim());
      results.tabs = tabs;
      
      // Check for flight cards
      results.flightCards = document.querySelectorAll('.flight-card').length;
      
      // Check for Trip Plan tab
      results.tripPlanTab = tabs.includes('Trip Plan');
      
      return results;
    `);
    
    console.log('Sidebar state:', JSON.stringify(sidebarState, null, 2));
    
    // Click on the sidebar toggle if sidebar is not visible
    if (!sidebarState.sidebarVisible || sidebarState.sidebarWidth < 100) {
      console.log('\n📝 Clicking sidebar toggle...');
      try {
        const sidebarToggle = await driver.findElement(By.css('.sidebar-toggle'));
        await sidebarToggle.click();
        await driver.sleep(2000);
      } catch (e) {
        console.log('Could not find sidebar toggle');
      }
    }
    
    // Re-check sidebar
    const sidebarStateAfter = await driver.executeScript(`
      const sidebar = document.querySelector('.search-results-sidebar');
      return {
        visible: sidebar ? window.getComputedStyle(sidebar).display !== 'none' : false,
        width: sidebar ? sidebar.offsetWidth : 0,
        innerHTML: sidebar ? sidebar.innerHTML.substring(0, 300) + '...' : 'no sidebar'
      };
    `);
    
    console.log('\nSidebar after toggle:', JSON.stringify(sidebarStateAfter, null, 2));
    
    // Try to click Trip Plan tab
    console.log('\n📝 Looking for Trip Plan tab...');
    try {
      const tripPlanTab = await driver.findElement(By.xpath("//button[contains(text(), 'Trip Plan')]"));
      await driver.executeScript("arguments[0].scrollIntoView(true);", tripPlanTab);
      await tripPlanTab.click();
      console.log('✅ Clicked Trip Plan tab');
      await driver.sleep(2000);
    } catch (e) {
      console.log('❌ Could not find Trip Plan tab:', e.message);
    }
    
    // Check for TripPlanPanel
    console.log('\n📝 Checking Trip Plan Panel');
    console.log('─'.repeat(40));
    
    const tripPlanState = await driver.executeScript(`
      return {
        tripPlanPanel: document.querySelectorAll('.trip-plan-panel').length,
        itineraryItems: document.querySelectorAll('.itinerary-item').length,
        tripPlanContent: document.querySelector('.trip-plan-panel')?.innerHTML?.substring(0, 200) || 'not found'
      };
    `);
    
    console.log('Trip plan state:', JSON.stringify(tripPlanState, null, 2));
    
    // Take final screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-mock-test.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as trip-plan-mock-test.png');
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Sidebar exists: ${sidebarState.sidebarExists ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip Plan tab exists: ${sidebarState.tripPlanTab ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip Plan panel renders: ${tripPlanState.tripPlanPanel > 0 ? 'PASS' : 'FAIL'}`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('trip-plan-mock-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as trip-plan-mock-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
tripPlanWithMockDataTest().catch(console.error);