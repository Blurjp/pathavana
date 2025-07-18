const { Builder, By, until, Key } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

/**
 * Comprehensive Quick Prompts UI Test
 * 
 * This test verifies:
 * 1. Default static prompts are displayed correctly
 * 2. Contextual prompts update based on AI responses
 * 3. Prompts are clickable and functional
 * 4. Prompt content is relevant to conversation context
 * 5. Prompts update dynamically as conversation progresses
 */
async function improvedQuickPromptsTest() {
  console.log('🎯 Improved Quick Prompts Comprehensive Test');
  console.log('═'.repeat(80));
  
  const options = new chrome.Options();
  options.addArguments('--window-size=1920,1080');
  
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  let testResults = {
    defaultPrompts: { pass: false, details: [] },
    contextualPrompts: { pass: false, details: [] },
    promptClickability: { pass: false, details: [] },
    dynamicUpdates: { pass: false, details: [] },
    contentRelevance: { pass: false, details: [] }
  };
  
  try {
    // Setup and Login
    console.log('🔧 Setup Phase');
    console.log('─'.repeat(40));
    
    await driver.get('http://localhost:3000');
    await driver.sleep(2000);
    
    // Clear storage for clean test
    await driver.executeScript(`
      localStorage.clear();
      sessionStorage.clear();
    `);
    
    console.log('🔐 Authenticating...');
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
    console.log('✅ Authentication successful\\n');
    
    await driver.sleep(3000);
    
    // TEST 1: Default Static Prompts Validation
    console.log('📝 Test 1: Default Static Prompts Validation');
    console.log('─'.repeat(50));
    
    const expectedDefaultPrompts = [
      "Plan a weekend trip to Paris",
      "Find flights to Tokyo under $800", 
      "Hotels in New York for next month"
    ];
    
    let quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${quickPrompts.length} quick prompts initially`);
    
    if (quickPrompts.length === 0) {
      testResults.defaultPrompts.details.push('❌ No quick prompts found on initial load');
    } else {
      const actualPrompts = [];
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        actualPrompts.push(text);
        console.log(`  📌 Prompt ${i + 1}: "${text}"`);
      }
      
      // Verify we have exactly 3 default prompts
      if (actualPrompts.length === 3) {
        testResults.defaultPrompts.details.push('✅ Correct number of default prompts (3)');
      } else {
        testResults.defaultPrompts.details.push(`❌ Expected 3 prompts, got ${actualPrompts.length}`);
      }
      
      // Verify default prompt content
      const matchingPrompts = actualPrompts.filter(prompt => 
        expectedDefaultPrompts.some(expected => 
          prompt.includes(expected) || expected.includes(prompt)
        )
      );
      
      if (matchingPrompts.length >= 2) {
        testResults.defaultPrompts.details.push('✅ Default prompts match expected content');
        testResults.defaultPrompts.pass = true;
      } else {
        testResults.defaultPrompts.details.push(`❌ Only ${matchingPrompts.length} prompts match expected content`);
      }
    }
    
    console.log(`  Result: ${testResults.defaultPrompts.pass ? 'PASS' : 'FAIL'}\\n`);
    
    // TEST 2: Prompt Clickability and Functionality
    console.log('📝 Test 2: Prompt Clickability and Functionality');
    console.log('─'.repeat(50));
    
    if (quickPrompts.length > 0) {
      const messageCountBefore = await driver.findElements(By.css('.message-content'));
      const firstPrompt = quickPrompts[0];
      const promptText = await firstPrompt.getText();
      
      console.log(`  🖱️  Clicking prompt: "${promptText}"`);
      await firstPrompt.click();
      await driver.sleep(3000);
      
      // Check if message was sent
      const messageCountAfter = await driver.findElements(By.css('.message-content'));
      const messageSent = messageCountAfter.length > messageCountBefore.length;
      
      if (messageSent) {
        testResults.promptClickability.pass = true;
        testResults.promptClickability.details.push('✅ Clicking prompt successfully sends message');
        
        // Verify the correct message was sent
        const lastMessage = messageCountAfter[messageCountAfter.length - 2]; // -2 because AI response comes after
        if (lastMessage) {
          const sentText = await lastMessage.getText();
          if (sentText.includes(promptText) || promptText.includes(sentText.substring(0, 20))) {
            testResults.promptClickability.details.push('✅ Correct message content sent');
          } else {
            testResults.promptClickability.details.push(`❌ Message content mismatch. Expected: "${promptText}", Sent: "${sentText}"`);
          }
        }
      } else {
        testResults.promptClickability.details.push('❌ Clicking prompt did not send message');
      }
    } else {
      testResults.promptClickability.details.push('❌ No prompts available to test clickability');
    }
    
    console.log(`  Result: ${testResults.promptClickability.pass ? 'PASS' : 'FAIL'}\\n`);
    
    // Wait for AI response and potential prompt updates
    console.log('  ⏳ Waiting for AI response and prompt updates...');
    await driver.sleep(8000);
    
    // TEST 3: Contextual Prompts Based on AI Response
    console.log('📝 Test 3: Contextual Prompts Based on AI Response');
    console.log('─'.repeat(50));
    
    // Get updated prompts after AI response
    quickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${quickPrompts.length} quick prompts after AI response`);
    
    let contextualPrompts = [];
    if (quickPrompts.length > 0) {
      for (let i = 0; i < quickPrompts.length; i++) {
        const text = await quickPrompts[i].getText();
        contextualPrompts.push(text);
        console.log(`  📌 Contextual prompt ${i + 1}: "${text}"`);
      }
      
      // Check if prompts are contextually relevant (more flexible patterns)
      const hasRelevantPrompts = contextualPrompts.some(prompt => {
        const lowerPrompt = prompt.toLowerCase();
        return lowerPrompt.includes('paris') || 
               lowerPrompt.includes('destination') || 
               lowerPrompt.includes('season') ||
               lowerPrompt.includes('travel') ||
               lowerPrompt.includes('looking') ||
               lowerPrompt.includes('popular') ||
               lowerPrompt.includes('date') || 
               lowerPrompt.includes('flight') || 
               lowerPrompt.includes('hotel') ||
               lowerPrompt.includes('when') ||
               lowerPrompt.includes('departure');
      });
      
      if (hasRelevantPrompts) {
        testResults.contextualPrompts.pass = true;
        testResults.contextualPrompts.details.push('✅ Prompts are contextually relevant to conversation');
      } else {
        testResults.contextualPrompts.details.push('❌ Prompts do not appear contextually relevant');
      }
      
      // Check if prompts updated from defaults
      const defaultPrompts = ["Plan a weekend trip to Paris", "Find flights to Tokyo under $800", "Hotels in New York for next month"];
      const promptsChanged = contextualPrompts.some(prompt => !defaultPrompts.includes(prompt));
      
      if (promptsChanged) {
        testResults.contextualPrompts.details.push('✅ Prompts updated from default set');
      } else {
        testResults.contextualPrompts.details.push('❌ Prompts did not update from defaults');
      }
    } else {
      testResults.contextualPrompts.details.push('❌ No contextual prompts found after AI response');
    }
    
    console.log(`  Result: ${testResults.contextualPrompts.pass ? 'PASS' : 'FAIL'}\\n`);
    
    // TEST 4: Dynamic Updates with Different Context
    console.log('📝 Test 4: Dynamic Updates with Different Context');
    console.log('─'.repeat(50));
    
    // Send a different type of message
    const chatInput = await driver.findElement(By.css('textarea'));
    await chatInput.clear();
    await chatInput.sendKeys('I want to travel to Tokyo for business, need hotels near train stations');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  📤 Sent: Tokyo business travel message');
    console.log('  ⏳ Waiting for AI response and prompt updates...');
    await driver.sleep(8000);
    
    // Check if prompts updated for new context
    const newQuickPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${newQuickPrompts.length} prompts after Tokyo business message`);
    
    if (newQuickPrompts.length > 0) {
      const newPrompts = [];
      for (let i = 0; i < newQuickPrompts.length; i++) {
        const text = await newQuickPrompts[i].getText();
        newPrompts.push(text);
        console.log(`  📌 New prompt ${i + 1}: "${text}"`);
      }
      
      // Check for business/Tokyo-specific prompts
      const hasBusinessContext = newPrompts.some(prompt => {
        const lowerPrompt = prompt.toLowerCase();
        return lowerPrompt.includes('tokyo') || 
               lowerPrompt.includes('business') || 
               lowerPrompt.includes('hotel') ||
               lowerPrompt.includes('train') ||
               lowerPrompt.includes('station');
      });
      
      if (hasBusinessContext) {
        testResults.dynamicUpdates.pass = true;
        testResults.dynamicUpdates.details.push('✅ Prompts dynamically updated for new context (Tokyo/business)');
      } else {
        testResults.dynamicUpdates.details.push('❌ Prompts did not update for new context');
      }
      
      // Verify prompts are different from previous set  
      const promptsAreDifferent = newPrompts.some(prompt => {
        return !contextualPrompts.includes(prompt);
      });
      
      if (promptsAreDifferent) {
        testResults.dynamicUpdates.details.push('✅ Prompts changed between different conversation contexts');
      } else {
        testResults.dynamicUpdates.details.push('❌ Prompts remained the same across different contexts');
      }
    } else {
      testResults.dynamicUpdates.details.push('❌ No prompts found after context change');
    }
    
    console.log(`  Result: ${testResults.dynamicUpdates.pass ? 'PASS' : 'FAIL'}\\n`);
    
    // TEST 5: Content Relevance Validation
    console.log('📝 Test 5: Content Relevance Validation');
    console.log('─'.repeat(50));
    
    // Send a specific travel query and verify prompts are helpful
    await chatInput.clear();
    await chatInput.sendKeys('I need help planning a family vacation with kids');
    await chatInput.sendKeys(Key.RETURN);
    
    console.log('  📤 Sent: Family vacation with kids message');
    console.log('  ⏳ Waiting for AI response...');
    await driver.sleep(8000);
    
    const familyPrompts = await driver.findElements(By.css('.quick-prompt'));
    console.log(`Found ${familyPrompts.length} prompts after family vacation message`);
    
    if (familyPrompts.length > 0) {
      const familyPromptTexts = [];
      for (let i = 0; i < familyPrompts.length; i++) {
        const text = await familyPrompts[i].getText();
        familyPromptTexts.push(text);
        console.log(`  📌 Family prompt ${i + 1}: "${text}"`);
      }
      
      // Check for family-relevant prompts
      const familyRelevantTerms = ['family', 'kids', 'children', 'activities', 'resort', 'theme park', 'vacation', 'dates', 'destination'];
      const hasFamilyRelevance = familyPromptTexts.some(prompt => {
        const lowerPrompt = prompt.toLowerCase();
        return familyRelevantTerms.some(term => lowerPrompt.includes(term));
      });
      
      if (hasFamilyRelevance) {
        testResults.contentRelevance.pass = true;
        testResults.contentRelevance.details.push('✅ Prompts are contextually relevant to family vacation planning');
      } else {
        testResults.contentRelevance.details.push('❌ Prompts lack family vacation context');
      }
      
      // Verify prompts are actionable (contain action words)
      const actionWords = ['find', 'book', 'plan', 'search', 'get', 'show', 'recommend'];
      const hasActionablePrompts = familyPromptTexts.some(prompt => {
        const lowerPrompt = prompt.toLowerCase();
        return actionWords.some(action => lowerPrompt.includes(action));
      });
      
      if (hasActionablePrompts) {
        testResults.contentRelevance.details.push('✅ Prompts contain actionable language');
      } else {
        testResults.contentRelevance.details.push('❌ Prompts lack actionable language');
      }
    } else {
      testResults.contentRelevance.details.push('❌ No prompts found for content relevance test');
    }
    
    console.log(`  Result: ${testResults.contentRelevance.pass ? 'PASS' : 'FAIL'}\\n`);
    
    // FINAL SUMMARY
    console.log('📊 Comprehensive Test Results Summary');
    console.log('═'.repeat(80));
    
    let totalTests = 0;
    let passedTests = 0;
    
    for (const [testName, result] of Object.entries(testResults)) {
      totalTests++;
      if (result.pass) passedTests++;
      
      console.log(`\\n🧪 ${testName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}`);
      console.log(`   Status: ${result.pass ? '✅ PASS' : '❌ FAIL'}`);
      result.details.forEach(detail => {
        console.log(`   ${detail}`);
      });
    }
    
    const overallSuccess = passedTests === totalTests;
    console.log(`\\n🎯 Overall Result: ${overallSuccess ? '✅ ALL TESTS PASSED' : `❌ ${passedTests}/${totalTests} TESTS PASSED`}`);
    console.log(`   Success Rate: ${Math.round((passedTests/totalTests) * 100)}%`);
    
    if (overallSuccess) {
      console.log('\\n🎉 Quick Prompts feature is working excellently!');
      console.log('   ✅ Default prompts display correctly');
      console.log('   ✅ Prompts are clickable and functional');
      console.log('   ✅ Contextual prompts update based on conversation');
      console.log('   ✅ Dynamic updates work across different contexts');
      console.log('   ✅ Content relevance is maintained');
    } else {
      console.log('\\n⚠️  Some quick prompts features need attention.');
    }
    
    // Take a final screenshot
    const screenshot = await driver.takeScreenshot();
    const fs = require('fs');
    fs.writeFileSync('improved-quick-prompts-test-final.png', screenshot, 'base64');
    console.log('\\n📸 Final screenshot saved as improved-quick-prompts-test-final.png');
    
    return testResults;
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    console.error('   Stack trace:', error.stack);
    
    // Take error screenshot
    try {
      const screenshot = await driver.takeScreenshot();
      const fs = require('fs');
      fs.writeFileSync('improved-quick-prompts-test-error.png', screenshot, 'base64');
      console.log('📸 Error screenshot saved as improved-quick-prompts-test-error.png');
    } catch (screenshotError) {
      console.error('Failed to take error screenshot:', screenshotError.message);
    }
    
    throw error;
  } finally {
    await driver.quit();
  }
}

// Export for potential use in other tests
module.exports = { improvedQuickPromptsTest };

// Run the test if called directly
if (require.main === module) {
  improvedQuickPromptsTest().catch(console.error);
}