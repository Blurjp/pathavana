#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

console.log('🔧 Preparing Selenium UI Test...\n');

// Check if Chrome is installed
try {
  if (process.platform === 'darwin') {
    execSync('ls /Applications/Google\\ Chrome.app', { stdio: 'ignore' });
  } else if (process.platform === 'win32') {
    execSync('where chrome', { stdio: 'ignore' });
  } else {
    execSync('which google-chrome || which chromium-browser', { stdio: 'ignore' });
  }
  console.log('✅ Chrome browser detected');
} catch (e) {
  console.error('❌ Chrome browser not found. Please install Chrome to run Selenium tests.');
  process.exit(1);
}

// Check if the application is running
const http = require('http');
const checkServer = (callback) => {
  const options = {
    hostname: 'localhost',
    port: 3000,
    path: '/',
    method: 'GET',
    timeout: 2000
  };
  
  const req = http.request(options, (res) => {
    callback(res.statusCode === 200 || res.statusCode === 304);
  });
  
  req.on('error', () => callback(false));
  req.on('timeout', () => {
    req.destroy();
    callback(false);
  });
  
  req.end();
};

checkServer((isRunning) => {
  if (!isRunning) {
    console.error('❌ Frontend server is not running on http://localhost:3000');
    console.error('   Please run: npm start');
    process.exit(1);
  }
  
  console.log('✅ Frontend server is running');
  console.log('✅ Starting Selenium test...\n');
  
  // Compile and run the TypeScript test
  try {
    // Compile TypeScript
    console.log('📦 Compiling TypeScript test...');
    execSync('npx tsc src/tests/e2e/TravelPlanUITest.ts --outDir build-test --esModuleInterop --module commonjs --target es2017', {
      stdio: 'inherit'
    });
    
    // Run the compiled test
    console.log('\n🚀 Running Selenium test...\n');
    require('./build-test/src/tests/e2e/TravelPlanUITest.js');
    
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    process.exit(1);
  }
});