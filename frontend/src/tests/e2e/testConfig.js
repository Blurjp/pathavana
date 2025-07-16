/**
 * Test Configuration for Selenium UI Tests
 * Centralized configuration for all test settings
 */

module.exports = {
  // Test User Credentials
  testUser: {
    email: 'selenium.test@example.com',
    password: 'SeleniumTest123!',
    fullName: 'Selenium Test User'
  },
  
  // URLs
  urls: {
    frontend: 'http://localhost:3000',
    backend: 'http://localhost:8001'
  },
  
  // Timeouts (in milliseconds)
  timeouts: {
    pageLoad: 10000,
    elementWait: 10000,
    aiResponse: 90000,  // 90 seconds for AI to generate travel plan
    animation: 1000
  },
  
  // Test Data
  testData: {
    travelRequest: "Create a comprehensive 5-day travel plan to Tokyo, Japan. I'm flying from San Francisco. " +
                   "Please include flight options, hotel recommendations in Shibuya area, " +
                   "and a daily itinerary with must-see attractions, local restaurants, and cultural experiences. " +
                   "My budget is around $3000 per person.",
    
    simpleRequest: "Create a 3-day travel plan to Paris, France including flights, hotels, and attractions."
  },
  
  // Chrome Options
  chromeOptions: [
    '--window-size=1920,1080',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor'
  ],
  
  // Selectors
  selectors: {
    // Authentication
    signInButton: '.auth-buttons button:first-child, button.btn-secondary',
    emailInput: 'input[type="email"], input[name="email"], input[placeholder*="email" i]',
    passwordInput: 'input[type="password"], input[name="password"]',
    userAvatar: '.user-avatar, .avatar-placeholder',
    
    // Navigation
    chatLink: 'a[href="/chat"], .nav-menu a:first-child',
    
    // Chat
    chatInput: [
      'textarea[placeholder*="Type your message"]',
      'textarea[placeholder*="Ask me"]',
      'textarea[placeholder*="travel"]',
      '.chat-input textarea',
      '.chat-input input',
      'textarea'
    ],
    
    sendButton: 'button[type="submit"], button[aria-label*="send" i], .chat-input button',
    
    // AI Response
    aiMessage: [
      '.message-content.assistant',
      '.chat-message.assistant',
      '.message.assistant',
      '[data-role="assistant"]',
      '.ai-message',
      '.bot-message'
    ],
    
    // Trip Plan
    tripPlanPanel: [
      '.trip-plan-panel',
      '.travel-plan-panel',
      '.sidebar-content',
      '.search-results-sidebar',
      '.trip-details',
      '[class*="trip-plan"]'
    ],
    
    sidebarToggle: '.sidebar-toggle, button[aria-label*="sidebar"], button[aria-label*="results"]'
  }
};