const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to check why sidebar is not rendering
 */
async function checkSidebarRenderTest() {
  console.log('🔍 Check Sidebar Render Test');
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
    
    // Check DOM structure
    console.log('📝 Checking DOM Structure');
    console.log('─'.repeat(40));
    
    const domStructure = await driver.executeScript(`
      const results = {
        chatPage: {
          exists: !!document.querySelector('.unified-travel-request-page'),
          classes: document.querySelector('.unified-travel-request-page')?.className || 'not found'
        },
        chatContainer: {
          exists: !!document.querySelector('.chat-container'),
          classes: document.querySelector('.chat-container')?.className || 'not found'
        },
        sidebarSearch: {
          byClass: document.querySelectorAll('.search-results-sidebar').length,
          byComponent: document.querySelectorAll('[class*="SearchResultsSidebar"]').length,
          anyClassWithSidebar: document.querySelectorAll('[class*="sidebar"]').length
        },
        reactRoot: {
          exists: !!document.querySelector('#root'),
          children: document.querySelector('#root')?.children.length || 0
        }
      };
      
      // Get all elements with class containing 'sidebar'
      const sidebarElements = Array.from(document.querySelectorAll('*')).filter(el => 
        el.className && el.className.toString().toLowerCase().includes('sidebar')
      );
      
      results.allSidebarElements = sidebarElements.map(el => ({
        tag: el.tagName,
        class: el.className,
        id: el.id || 'no-id'
      }));
      
      return results;
    `);
    
    console.log('DOM Structure:', JSON.stringify(domStructure, null, 2));
    
    // Send message to trigger search
    console.log('\n📝 Sending search message...');
    const chatInput = await driver.wait(
      until.elementLocated(By.css('textarea')),
      5000
    );
    await chatInput.clear();
    await chatInput.sendKeys('Find flights from San Francisco to Tokyo on March 15');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('⏳ Waiting for response...');
    await driver.sleep(10000);
    
    // Check DOM after search
    console.log('\n📝 DOM After Search');
    console.log('─'.repeat(40));
    
    const domAfterSearch = await driver.executeScript(`
      const results = {
        sidebar: {
          searchResultsSidebar: document.querySelectorAll('.search-results-sidebar').length,
          anySidebar: document.querySelectorAll('[class*="sidebar"]').length
        },
        searchRelated: {
          searchProgress: document.querySelectorAll('.search-progress').length,
          flightCards: document.querySelectorAll('.flight-card').length,
          searchSummary: document.querySelectorAll('.search-summary').length
        },
        messages: {
          total: document.querySelectorAll('.message').length,
          assistant: document.querySelectorAll('.message.assistant').length,
          user: document.querySelectorAll('.message.user').length
        }
      };
      
      // Check if UnifiedTravelRequest page has sidebar-open class
      const chatPage = document.querySelector('.unified-travel-request-page');
      results.chatPageClasses = chatPage ? chatPage.className : 'not found';
      
      // Get the HTML structure around where sidebar should be
      const root = document.querySelector('#root');
      if (root && root.firstChild) {
        results.rootStructure = {
          firstChildClass: root.firstChild.className || 'no-class',
          childCount: root.children.length,
          innerHTML: root.innerHTML.substring(0, 500) + '...'
        };
      }
      
      return results;
    `);
    
    console.log('DOM After Search:', JSON.stringify(domAfterSearch, null, 2));
    
    // Check React component tree if possible
    console.log('\n📝 Checking Component Rendering');
    console.log('─'.repeat(40));
    
    const componentCheck = await driver.executeScript(`
      // Try to find SearchResultsSidebar in the page source
      const pageSource = document.documentElement.innerHTML;
      return {
        hasSearchResultsSidebarInSource: pageSource.includes('SearchResultsSidebar'),
        hasSidebarContextInSource: pageSource.includes('SidebarContext'),
        hasUnifiedTravelRequestInSource: pageSource.includes('UnifiedTravelRequest')
      };
    `);
    
    console.log('Component Check:', JSON.stringify(componentCheck, null, 2));
    
    // Take screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('check-sidebar-render.png', screenshot, 'base64');
    console.log('\n📸 Screenshot saved as check-sidebar-render.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('check-sidebar-render-error.png', screenshot, 'base64');
    console.log('📸 Error screenshot saved as check-sidebar-render-error.png');
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
checkSidebarRenderTest().catch(console.error);