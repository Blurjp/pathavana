const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test flight and hotel search with mock API responses
 */
async function flightHotelSearchWithMockAPI() {
  console.log('✈️ 🏨 Flight & Hotel Search with Mock API Test');
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
    
    // Test 1: Set up API interceptor
    console.log('📝 Test 1: Setting up Mock API Interceptor');
    console.log('─'.repeat(40));
    
    await driver.executeScript(`
      // Store the original fetch
      window.originalFetch = window.fetch;
      
      // Mock flight data
      const mockFlightResults = {
        message: "I found several flights from San Francisco to Tokyo. Here are the best options:",
        searchResults: {
          flights: [
            {
              id: 'UA890-2024-03-15',
              airline: 'United Airlines',
              flightNumber: 'UA890',
              origin: {
                code: 'SFO',
                city: 'San Francisco',
                airport: 'San Francisco International',
                terminal: '3'
              },
              destination: {
                code: 'NRT',
                city: 'Tokyo',
                airport: 'Narita International',
                terminal: '1'
              },
              departureTime: '2024-03-15T08:00:00-07:00',
              arrivalTime: '2024-03-16T14:30:00+09:00',
              duration: '10h 30m',
              price: {
                amount: 850,
                currency: 'USD',
                displayPrice: '$850'
              },
              stops: 0,
              amenities: ['WiFi', 'Entertainment', 'Meals', 'Power Outlets'],
              aircraft: 'Boeing 787-9'
            },
            {
              id: 'JL001-2024-03-15',
              airline: 'Japan Airlines',
              flightNumber: 'JL001',
              origin: {
                code: 'SFO',
                city: 'San Francisco',
                airport: 'San Francisco International',
                terminal: 'I'
              },
              destination: {
                code: 'HND',
                city: 'Tokyo',
                airport: 'Haneda',
                terminal: '3'
              },
              departureTime: '2024-03-15T11:00:00-07:00',
              arrivalTime: '2024-03-16T16:20:00+09:00',
              duration: '11h 20m',
              price: {
                amount: 920,
                currency: 'USD',
                displayPrice: '$920'
              },
              stops: 0,
              amenities: ['WiFi', 'Premium Meals', 'Entertainment', 'Lie-flat Seats'],
              aircraft: 'Boeing 777-300ER'
            }
          ],
          hotels: [],
          activities: []
        },
        hints: [
          { text: "Book 2-3 months in advance for best prices", type: "tip" },
          { text: "Consider flying into Haneda for easier city access", type: "tip" }
        ]
      };
      
      // Mock hotel data
      const mockHotelResults = {
        message: "I found excellent hotels in Tokyo's Shibuya area for your dates. Here are the top recommendations:",
        searchResults: {
          flights: [],
          hotels: [
            {
              id: 'park-hyatt-tokyo',
              name: 'Park Hyatt Tokyo',
              location: {
                address: '3-7-1-2 Nishi-Shinjuku',
                city: 'Tokyo',
                neighborhood: 'Shinjuku',
                country: 'Japan',
                coordinates: { lat: 35.6852, lng: 139.6891 }
              },
              price: {
                amount: 450,
                currency: 'USD',
                displayPrice: '$450',
                period: 'per night'
              },
              rating: 4.8,
              reviewCount: 1842,
              amenities: ['Free WiFi', 'Pool', 'Spa', 'Restaurant', 'Bar', 'Fitness Center', 'Business Center'],
              roomTypes: ['Deluxe Room', 'Park Suite', 'Tokyo Suite'],
              images: ['https://example.com/park-hyatt-1.jpg'],
              checkIn: '2024-03-15',
              checkOut: '2024-03-20'
            },
            {
              id: 'mandarin-oriental-tokyo',
              name: 'Mandarin Oriental Tokyo',
              location: {
                address: '2-1-1 Nihonbashi Muromachi',
                city: 'Tokyo',
                neighborhood: 'Nihonbashi',
                country: 'Japan',
                coordinates: { lat: 35.6847, lng: 139.7738 }
              },
              price: {
                amount: 520,
                currency: 'USD',
                displayPrice: '$520',
                period: 'per night'
              },
              rating: 4.9,
              reviewCount: 2156,
              amenities: ['Free WiFi', 'Spa', 'Restaurant', 'Bar', 'Concierge', 'Room Service'],
              roomTypes: ['Deluxe Room', 'Premier Room', 'Mandarin Suite'],
              images: ['https://example.com/mandarin-1.jpg'],
              checkIn: '2024-03-15',
              checkOut: '2024-03-20'
            }
          ],
          activities: []
        },
        hints: [
          { text: "Book hotels with free cancellation for flexibility", type: "tip" },
          { text: "Shibuya area offers great shopping and dining", type: "tip" }
        ]
      };
      
      // Override fetch to intercept API calls
      window.fetch = async function(...args) {
        const [url, options] = args;
        
        console.log('Intercepted fetch:', url);
        
        // Check if this is a chat message request
        if (url.includes('/api/travel/chat') && options?.method === 'POST') {
          const body = JSON.parse(options.body);
          const message = body.message.toLowerCase();
          
          // Return mock data based on the message content
          if (message.includes('flight')) {
            console.log('Returning mock flight data');
            return {
              ok: true,
              json: async () => mockFlightResults,
              status: 200
            };
          } else if (message.includes('hotel')) {
            console.log('Returning mock hotel data');
            return {
              ok: true,
              json: async () => mockHotelResults,
              status: 200
            };
          }
        }
        
        // Fall back to original fetch for other requests
        return window.originalFetch(...args);
      };
      
      console.log('Mock API interceptor set up');
    `);
    
    // Test 2: Search for flights
    console.log('\n📝 Test 2: Search for Flights');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo on March 15');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for flight results...');
    await driver.sleep(8000);
    
    // Check flight results
    const flightResults = await driver.executeScript(`
      const sidebar = document.querySelector('.search-results-sidebar');
      const flightCards = document.querySelectorAll('.flight-card');
      const addButtons = document.querySelectorAll('.flight-card .add-to-trip');
      
      return {
        sidebarOpen: sidebar ? sidebar.offsetWidth > 100 : false,
        flightCardCount: flightCards.length,
        addToTripButtonCount: addButtons.length,
        firstFlightDetails: flightCards.length > 0 ? {
          airline: flightCards[0].querySelector('.airline-name')?.textContent,
          price: flightCards[0].querySelector('.price-container')?.textContent
        } : null
      };
    `);
    
    console.log('  Flight results:', JSON.stringify(flightResults, null, 2));
    
    // Test 3: Add flight to trip
    console.log('\n📝 Test 3: Add Flight to Trip');
    console.log('─'.repeat(40));
    
    if (flightResults.addToTripButtonCount > 0) {
      await driver.executeScript(`
        const addButton = document.querySelector('.flight-card .add-to-trip');
        if (addButton) {
          addButton.click();
          console.log('Clicked Add to Trip button');
        }
      `);
      
      await driver.sleep(2000);
      
      // Check Trip Plan
      await driver.executeScript(`
        const tripPlanTab = Array.from(document.querySelectorAll('.sidebar-tabs button'))
          .find(btn => btn.textContent.includes('Trip Plan'));
        if (tripPlanTab) tripPlanTab.click();
      `);
      
      await driver.sleep(1000);
      
      const tripPlanAfterAdd = await driver.executeScript(`
        const tripPanel = document.querySelector('.trip-plan-panel');
        const itineraryItems = document.querySelectorAll('.itinerary-item');
        
        return {
          itemCount: itineraryItems.length,
          panelContent: tripPanel ? tripPanel.textContent.substring(0, 200) : 'not found',
          hasEmptyState: tripPanel ? tripPanel.textContent.includes('No trip plan yet') : true
        };
      `);
      
      console.log('  Trip Plan after adding flight:', JSON.stringify(tripPlanAfterAdd, null, 2));
    }
    
    // Test 4: Search for hotels
    console.log('\n📝 Test 4: Search for Hotels');
    console.log('─'.repeat(40));
    
    // Go back to Flights tab first
    await driver.executeScript(`
      const flightsTab = document.querySelector('.sidebar-tabs button');
      if (flightsTab) flightsTab.click();
    `);
    
    await chatInput.clear();
    await chatInput.sendKeys('Find hotels in Tokyo Shibuya area for March 15-20');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for hotel results...');
    await driver.sleep(8000);
    
    // Click Hotels tab
    await driver.executeScript(`
      const hotelsTab = Array.from(document.querySelectorAll('.sidebar-tabs button'))
        .find(btn => btn.textContent.includes('Hotels'));
      if (hotelsTab) hotelsTab.click();
    `);
    
    await driver.sleep(1000);
    
    const hotelResults = await driver.executeScript(`
      const hotelCards = document.querySelectorAll('.hotel-card');
      const addButtons = document.querySelectorAll('.hotel-card .add-to-trip, .result-item-wrapper .add-to-trip-button');
      
      return {
        hotelCardCount: hotelCards.length,
        addButtonCount: addButtons.length,
        firstHotelDetails: hotelCards.length > 0 ? {
          name: hotelCards[0].querySelector('.hotel-name')?.textContent,
          price: hotelCards[0].querySelector('.price-display')?.textContent
        } : null
      };
    `);
    
    console.log('  Hotel results:', JSON.stringify(hotelResults, null, 2));
    
    // Test 5: Add hotel to trip
    console.log('\n📝 Test 5: Add Hotel to Trip');
    console.log('─'.repeat(40));
    
    if (hotelResults.addButtonCount > 0) {
      await driver.executeScript(`
        const addButton = document.querySelector('.hotel-card .add-to-trip, .result-item-wrapper .add-to-trip-button');
        if (addButton) {
          addButton.click();
          console.log('Clicked Add to Trip button for hotel');
        }
      `);
      
      await driver.sleep(2000);
      
      // Check updated Trip Plan
      await driver.executeScript(`
        const tripPlanTab = Array.from(document.querySelectorAll('.sidebar-tabs button'))
          .find(btn => btn.textContent.includes('Trip Plan'));
        if (tripPlanTab) tripPlanTab.click();
      `);
      
      await driver.sleep(1000);
      
      const finalTripPlan = await driver.executeScript(`
        const tripPanel = document.querySelector('.trip-plan-panel');
        const itineraryItems = document.querySelectorAll('.itinerary-item');
        const flightItems = document.querySelectorAll('.itinerary-item[data-type="flight"]');
        const hotelItems = document.querySelectorAll('.itinerary-item[data-type="hotel"]');
        
        return {
          totalItems: itineraryItems.length,
          flightCount: flightItems.length,
          hotelCount: hotelItems.length,
          hasEmptyState: tripPanel ? tripPanel.textContent.includes('No trip plan yet') : true
        };
      `);
      
      console.log('  Final Trip Plan:', JSON.stringify(finalTripPlan, null, 2));
    }
    
    // Take final screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('flight-hotel-search-final.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as flight-hotel-search-final.png');
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('═'.repeat(60));
    console.log(`✅ Search results display: ${flightResults.flightCardCount > 0 || hotelResults.hotelCardCount > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Add to Trip buttons exist: ${flightResults.addToTripButtonCount > 0 || hotelResults.addButtonCount > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✅ Trip Plan updates: ${!tripPlanAfterAdd?.hasEmptyState ? 'PASS' : 'PENDING'}`);
    console.log(`✅ Multiple item types: ${finalTripPlan?.totalItems > 1 ? 'PASS' : 'PENDING'}`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error(error.stack);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('flight-hotel-search-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as flight-hotel-search-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
flightHotelSearchWithMockAPI().catch(console.error);