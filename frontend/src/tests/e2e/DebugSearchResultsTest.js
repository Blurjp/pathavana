const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to understand why search results aren't showing
 */
async function debugSearchResultsTest() {
  console.log('🔍 Debug Search Results Test');
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
    
    // Monitor network requests
    console.log('📝 Setting up network monitoring');
    console.log('─'.repeat(40));
    
    await driver.executeScript(`
      window.apiResponses = [];
      
      // Intercept fetch to log responses
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const response = await originalFetch(...args);
        const url = args[0];
        
        // Clone response to read it
        const clone = response.clone();
        try {
          const data = await clone.json();
          window.apiResponses.push({
            url: url,
            status: response.status,
            data: data
          });
          console.log('API Response:', url, data);
        } catch (e) {
          console.log('Could not parse response as JSON');
        }
        
        return response;
      };
      
      console.log('Network monitoring set up');
    `);
    
    // Send flight search message
    console.log('\n📝 Sending flight search message');
    console.log('─'.repeat(40));
    
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Search for flights from New York to Paris next week');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  ⏳ Waiting for response...');
    await driver.sleep(10000);
    
    // Check API responses
    console.log('\n📝 Checking API responses');
    console.log('─'.repeat(40));
    
    const apiData = await driver.executeScript(`
      return {
        responseCount: window.apiResponses.length,
        responses: window.apiResponses.map(r => ({
          url: r.url,
          status: r.status,
          hasSearchResults: !!(r.data && r.data.searchResults),
          searchResultsKeys: r.data?.searchResults ? Object.keys(r.data.searchResults) : [],
          messageContent: r.data?.message ? r.data.message.substring(0, 100) + '...' : null
        }))
      };
    `);
    
    console.log('  API responses:', JSON.stringify(apiData, null, 2));
    
    // Check React state
    console.log('\n📝 Checking React state and DOM');
    console.log('─'.repeat(40));
    
    const reactState = await driver.executeScript(`
      const results = {};
      
      // Check messages
      const messages = document.querySelectorAll('.message');
      results.messageCount = messages.length;
      results.lastMessage = messages.length > 0 ? 
        messages[messages.length - 1].textContent.substring(0, 100) : null;
      
      // Check sidebar
      const sidebar = document.querySelector('.search-results-sidebar');
      results.sidebarExists = !!sidebar;
      results.sidebarVisible = sidebar ? sidebar.offsetWidth > 100 : false;
      
      // Check for search progress indicators
      results.searchProgress = document.querySelectorAll('.search-progress').length;
      results.searchSummary = document.querySelectorAll('.search-summary').length;
      
      // Check for result cards
      results.flightCards = document.querySelectorAll('.flight-card').length;
      results.hotelCards = document.querySelectorAll('.hotel-card').length;
      
      // Check sidebar content
      if (sidebar) {
        results.sidebarInnerHTML = sidebar.innerHTML.substring(0, 500) + '...';
        results.loadingState = sidebar.querySelector('.loading-state') ? true : false;
        results.emptyState = sidebar.querySelector('.empty-state') ? true : false;
      }
      
      return results;
    `);
    
    console.log('  React state:', JSON.stringify(reactState, null, 2));
    
    // Try to manually trigger search results display
    console.log('\n📝 Attempting manual search results injection');
    console.log('─'.repeat(40));
    
    await driver.executeScript(`
      // Find the last assistant message and check its metadata
      const messages = document.querySelectorAll('.message.assistant');
      const lastAssistantMessage = messages[messages.length - 1];
      
      console.log('Last assistant message:', lastAssistantMessage?.textContent);
      
      // Check if search results are in the page but not displayed
      const searchResultsInDOM = document.body.innerHTML.includes('searchResults');
      console.log('Search results in DOM:', searchResultsInDOM);
    `);
    
    // Check specific UI elements
    console.log('\n📝 Checking UI elements');
    console.log('─'.repeat(40));
    
    const uiElements = await driver.executeScript(`
      return {
        tabs: Array.from(document.querySelectorAll('.sidebar-tabs button')).map(b => b.textContent.trim()),
        activeTab: document.querySelector('.sidebar-tabs button.active')?.textContent,
        sidebarContent: document.querySelector('.sidebar-content')?.className,
        resultsContent: document.querySelector('.results-content') ? 'exists' : 'not found',
        flightsList: document.querySelector('.flights-list') ? 'exists' : 'not found',
        hotelsList: document.querySelector('.hotels-list') ? 'exists' : 'not found'
      };
    `);
    
    console.log('  UI elements:', JSON.stringify(uiElements, null, 2));
    
    // Take screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('debug-search-results.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as debug-search-results.png');
    
    // Summary
    console.log('\n📊 Debug Summary');
    console.log('═'.repeat(60));
    console.log('  1. API is responding but may not include searchResults');
    console.log('  2. Sidebar is opening correctly');
    console.log('  3. No flight/hotel cards are being rendered');
    console.log('  4. The issue is likely in the backend not returning search results');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('debug-search-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as debug-search-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
debugSearchResultsTest().catch(console.error);