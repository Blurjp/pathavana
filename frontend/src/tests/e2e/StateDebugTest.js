const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Test to check component states preventing API calls
 */
async function stateDebugTest() {
  console.log('🔍 Component State Debug Test');
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
    
    // Wait for auth
    await driver.wait(until.urlContains('/chat'), 10000);
    console.log('✅ Logged in successfully');
    
    await driver.sleep(2000);
    
    // Add debugging to React components
    await driver.executeScript(`
      // Hook into React DevTools to inspect component state
      window.componentStates = [];
      
      // Try to find React fiber nodes
      const findReactFiber = (dom) => {
        const key = Object.keys(dom).find(key => key.startsWith('__reactFiber'));
        return dom[key];
      };
      
      // Find the chat input and trace up to find the component with state
      const chatInput = document.querySelector('textarea[placeholder*="travel"]');
      if (chatInput) {
        let fiber = findReactFiber(chatInput);
        let depth = 0;
        
        while (fiber && depth < 30) {
          if (fiber.memoizedState) {
            // This is a component with hooks
            let hookState = fiber.memoizedState;
            let hookIndex = 0;
            
            while (hookState) {
              window.componentStates.push({
                component: fiber.elementType?.name || 'Unknown',
                hookIndex: hookIndex,
                value: hookState.memoizedState
              });
              hookState = hookState.next;
              hookIndex++;
            }
          }
          
          fiber = fiber.return;
          depth++;
        }
      }
      
      console.log('Found component states:', window.componentStates.length);
    `);
    
    // Override sendMessage to log when it's called
    await driver.executeScript(`
      window.sendMessageCalls = [];
      
      // Find the chat input
      const chatInput = document.querySelector('textarea[placeholder*="travel"]');
      if (chatInput) {
        // Override the onKeyDown to track calls
        const originalOnKeyDown = chatInput.onkeydown;
        chatInput.onkeydown = function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
            window.sendMessageCalls.push({
              time: new Date().toISOString(),
              value: chatInput.value
            });
          }
          if (originalOnKeyDown) {
            return originalOnKeyDown.call(this, e);
          }
        };
      }
      
      // Also track any fetch calls
      const originalFetch = window.fetch;
      window.fetchCalls = [];
      window.fetch = function(...args) {
        window.fetchCalls.push({
          url: args[0],
          time: new Date().toISOString()
        });
        return originalFetch.apply(this, args);
      };
    `);
    
    // Find chat input
    const chatInput = await driver.findElement(By.css('textarea[placeholder*="travel"]'));
    console.log('✅ Found chat input');
    
    // Check if there's a loading state
    const loadingIndicators = await driver.findElements(By.css('.loading, .spinner, [class*="loading"]'));
    console.log(`\n⏳ Loading indicators found: ${loadingIndicators.length}`);
    
    // Send a message
    console.log('\n📝 Sending test message...');
    await chatInput.clear();
    await chatInput.sendKeys('Test message');
    
    // Check button state before sending
    const sendButton = await driver.findElement(By.css('button[type="submit"], button[aria-label*="Send"]'));
    const isDisabled = await sendButton.getAttribute('disabled');
    console.log(`Send button disabled: ${isDisabled}`);
    
    await chatInput.sendKeys(Key.RETURN);
    
    // Wait briefly
    await driver.sleep(2000);
    
    // Get debug info
    const debugInfo = await driver.executeScript(`
      return {
        sendMessageCalls: window.sendMessageCalls || [],
        fetchCalls: window.fetchCalls || [],
        componentStates: window.componentStates ? window.componentStates.slice(0, 10) : [],
        hasSessionId: !!localStorage.getItem('pathavana_session_id')
      };
    `);
    
    console.log('\n📊 Debug Info:');
    console.log(`SendMessage calls: ${debugInfo.sendMessageCalls.length}`);
    console.log(`Fetch calls: ${debugInfo.fetchCalls.length}`);
    console.log(`Has session ID: ${debugInfo.hasSessionId}`);
    
    if (debugInfo.sendMessageCalls.length > 0) {
      console.log('\nSendMessage calls:', debugInfo.sendMessageCalls);
    }
    
    if (debugInfo.fetchCalls.length > 0) {
      console.log('\nFetch calls:', debugInfo.fetchCalls);
    }
    
    // Check if message was added
    const messages = await driver.findElements(By.css('.message-content'));
    console.log(`\n📨 Total messages displayed: ${messages.length}`);
    
    console.log('\n✅ Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    await driver.quit();
  }
}

// Run the test
stateDebugTest().catch(console.error);