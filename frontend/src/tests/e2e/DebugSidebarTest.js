const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Debug test to understand sidebar behavior
 */
async function debugSidebarTest() {
  console.log('🔍 Debug Sidebar Test');
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
    
    // Debug initial state
    console.log('📝 Debug: Initial State');
    console.log('─'.repeat(40));
    
    const initialState = await driver.executeScript(`
      const sidebar = document.querySelector('.search-results-sidebar');
      const chatPage = document.querySelector('.unified-travel-request-page');
      
      return {
        sidebarExists: !!sidebar,
        sidebarClasses: sidebar ? sidebar.className : 'none',
        sidebarDisplay: sidebar ? window.getComputedStyle(sidebar).display : 'none',
        chatPageClasses: chatPage ? chatPage.className : 'none',
        hasSidebarOpenClass: chatPage ? chatPage.classList.contains('sidebar-open') : false
      };
    `);
    
    console.log('Initial state:', JSON.stringify(initialState, null, 2));
    
    // Send message
    console.log('\n📝 Sending flight search message...');
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo on March 15, 2024');
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait and check periodically
    console.log('\n⏳ Monitoring changes...');
    for (let i = 0; i < 10; i++) {
      await driver.sleep(2000);
      
      const state = await driver.executeScript(`
        const sidebar = document.querySelector('.search-results-sidebar');
        const chatPage = document.querySelector('.unified-travel-request-page');
        const messages = document.querySelectorAll('.message');
        const searchProgress = document.querySelectorAll('.search-progress');
        const flightCards = document.querySelectorAll('.flight-card');
        
        // Check React DevTools if available
        let reactState = null;
        try {
          const reactFiber = sidebar?._reactInternalFiber || sidebar?._reactInternalInstance;
          if (reactFiber) {
            reactState = 'React component detected';
          }
        } catch (e) {}
        
        return {
          time: ${i * 2}s,
          sidebarExists: !!sidebar,
          sidebarDisplay: sidebar ? window.getComputedStyle(sidebar).display : 'none',
          sidebarWidth: sidebar ? sidebar.offsetWidth : 0,
          hasSidebarOpenClass: chatPage ? chatPage.classList.contains('sidebar-open') : false,
          messageCount: messages.length,
          searchProgressCount: searchProgress.length,
          flightCardCount: flightCards.length,
          reactState: reactState
        };
      `);
      
      console.log(`\nState at ${state.time}:`, JSON.stringify(state, null, 2));
      
      // Check for specific elements
      if (state.flightCardCount > 0) {
        console.log('✅ Flight cards detected!');
        break;
      }
    }
    
    // Final comprehensive check
    console.log('\n📝 Final State Analysis');
    console.log('─'.repeat(40));
    
    const finalAnalysis = await driver.executeScript(`
      const results = {
        sidebar: {},
        searchResults: {},
        buttons: {},
        tabs: {}
      };
      
      // Sidebar analysis
      const sidebar = document.querySelector('.search-results-sidebar');
      if (sidebar) {
        results.sidebar = {
          exists: true,
          display: window.getComputedStyle(sidebar).display,
          visibility: window.getComputedStyle(sidebar).visibility,
          width: sidebar.offsetWidth,
          height: sidebar.offsetHeight,
          position: window.getComputedStyle(sidebar).position,
          innerHTML: sidebar.innerHTML.substring(0, 200) + '...'
        };
      } else {
        results.sidebar = { exists: false };
      }
      
      // Search results
      results.searchResults = {
        flightCards: document.querySelectorAll('.flight-card').length,
        hotelCards: document.querySelectorAll('.hotel-card').length,
        activityCards: document.querySelectorAll('.activity-card').length,
        searchResultsSidebar: document.querySelectorAll('.search-results-sidebar').length
      };
      
      // Buttons
      const allButtons = Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.textContent.trim(),
        classes: b.className,
        visible: b.offsetParent !== null
      }));
      
      results.buttons = {
        total: allButtons.length,
        tripPlanButton: allButtons.filter(b => b.text.includes('Trip Plan')),
        addToTripButtons: allButtons.filter(b => b.text.includes('Add to Trip') || b.classes.includes('add-to-trip'))
      };
      
      // Tabs
      results.tabs = {
        sidebarTabs: Array.from(document.querySelectorAll('.sidebar-tabs button')).map(b => b.textContent.trim())
      };
      
      return results;
    `);
    
    console.log('Final analysis:', JSON.stringify(finalAnalysis, null, 2));
    
    // Take screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('debug-sidebar-test.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as debug-sidebar-test.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('debug-sidebar-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as debug-sidebar-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
debugSidebarTest().catch(console.error);