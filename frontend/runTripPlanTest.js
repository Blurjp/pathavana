#!/usr/bin/env node

const { execSync } = require('child_process');
const http = require('http');
const path = require('path');

console.log('🚀 Pathavana Trip Plan Test Runner');
console.log('═'.repeat(50));

// Step 1: Check Chrome
console.log('\n1️⃣ Checking Chrome browser...');
try {
  if (process.platform === 'darwin') {
    execSync('ls /Applications/Google\\ Chrome.app', { stdio: 'ignore' });
  } else if (process.platform === 'win32') {
    execSync('where chrome', { stdio: 'ignore' });
  } else {
    execSync('which google-chrome || which chromium-browser', { stdio: 'ignore' });
  }
  console.log('   ✅ Chrome browser found');
} catch (e) {
  console.error('   ❌ Chrome browser not found');
  console.error('   Please install Chrome from: https://www.google.com/chrome/');
  process.exit(1);
}

// Step 2: Check Frontend
console.log('\n2️⃣ Checking frontend server...');
const checkFrontend = (callback) => {
  const req = http.request({
    hostname: 'localhost',
    port: 3000,
    path: '/',
    method: 'GET',
    timeout: 2000
  }, (res) => callback(true));
  
  req.on('error', () => callback(false));
  req.on('timeout', () => {
    req.destroy();
    callback(false);
  });
  req.end();
};

// Step 3: Check Backend
console.log('\n3️⃣ Checking backend server...');
const checkBackend = (callback) => {
  const req = http.request({
    hostname: 'localhost',
    port: 8001,
    path: '/health',
    method: 'GET',
    timeout: 2000
  }, (res) => callback(true));
  
  req.on('error', () => callback(false));
  req.on('timeout', () => {
    req.destroy();
    callback(false);
  });
  req.end();
};

// Check both servers
checkFrontend((frontendRunning) => {
  if (!frontendRunning) {
    console.error('   ❌ Frontend not running on http://localhost:3000');
    console.error('   Please run: npm start');
    process.exit(1);
  }
  console.log('   ✅ Frontend is running');
  
  checkBackend((backendRunning) => {
    if (!backendRunning) {
      console.error('   ❌ Backend not running on http://localhost:8001');
      console.error('   Please run:');
      console.error('   cd backend && source venv/bin/activate');
      console.error('   uvicorn app.main:app --reload --port 8001');
      process.exit(1);
    }
    console.log('   ✅ Backend is running');
    
    // Step 4: Setup test user
    console.log('\n4️⃣ Setting up test user...');
    try {
      const { createTestUser } = require('./src/tests/e2e/setupTestUser.js');
      createTestUser().then(() => {
        console.log('   ✅ Test user ready');
        
        // Step 5: Run the test
        console.log('\n5️⃣ Starting UI test...');
        console.log('═'.repeat(50));
        console.log('\n');
        
        // Run the trip plan creation test
        require('./src/tests/e2e/TripPlanCreationTest.js');
        
      }).catch(err => {
        console.error('   ❌ Test user setup failed:', err.message);
        process.exit(1);
      });
    } catch (e) {
      console.error('   ❌ Error setting up test user:', e.message);
      
      // Continue anyway - user might exist
      console.log('   ⚠️  Continuing with test...');
      console.log('\n5️⃣ Starting UI test...');
      console.log('═'.repeat(50));
      console.log('\n');
      
      require('./src/tests/e2e/TripPlanCreationTest.js');
    }
  });
});