#!/usr/bin/env node

const axios = require('axios');

const BASE_URL = 'http://localhost:8001';
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword',
  full_name: 'Test User'
};

async function checkBackendHealth() {
  try {
    const response = await axios.get(`${BASE_URL}/health`);
    return response.data.status === 'healthy' || response.data.status === 'degraded';
  } catch (e) {
    return false;
  }
}

async function createTestUser() {
  console.log('🔧 Setting up test user...\n');
  
  // Check backend is running
  console.log('📡 Checking backend connection...');
  const isHealthy = await checkBackendHealth();
  
  if (!isHealthy) {
    console.error('❌ Backend is not running on http://localhost:8001');
    console.error('   Please start the backend with:');
    console.error('   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8001');
    process.exit(1);
  }
  
  console.log('✅ Backend is running');
  
  // Try to login with test user
  console.log('\n🔐 Checking if test user exists...');
  
  try {
    const loginResponse = await axios.post(`${BASE_URL}/api/v1/auth/login`, {
      email: TEST_USER.email,
      password: TEST_USER.password
    });
    
    if (loginResponse.data.access_token) {
      console.log('✅ Test user already exists and can login');
      console.log(`   Email: ${TEST_USER.email}`);
      console.log(`   Password: ${TEST_USER.password}`);
      return;
    }
  } catch (e) {
    if (e.response && e.response.status === 401) {
      console.log('⚠️  Test user not found or invalid credentials');
    }
  }
  
  // Try to register test user
  console.log('\n📝 Attempting to create test user...');
  
  try {
    const registerResponse = await axios.post(`${BASE_URL}/api/v1/auth/register`, {
      email: TEST_USER.email,
      password: TEST_USER.password,
      full_name: TEST_USER.full_name
    });
    
    if (registerResponse.data.access_token) {
      console.log('✅ Test user created successfully!');
      console.log(`   Email: ${TEST_USER.email}`);
      console.log(`   Password: ${TEST_USER.password}`);
      return;
    }
  } catch (e) {
    if (e.response && e.response.status === 400) {
      console.log('ℹ️  User might already exist with different password');
    } else {
      console.error('❌ Failed to create test user:', e.message);
    }
  }
  
  console.log('\n📋 Manual Setup Instructions:');
  console.log('1. Create a test user with the following credentials:');
  console.log(`   Email: ${TEST_USER.email}`);
  console.log(`   Password: ${TEST_USER.password}`);
  console.log('\n2. Or update the test to use your existing credentials');
  console.log('\n3. Make sure the backend database is properly configured');
}

// Run if called directly
if (require.main === module) {
  createTestUser()
    .then(() => console.log('\n✅ Test user setup complete'))
    .catch(err => {
      console.error('\n❌ Setup failed:', err.message);
      process.exit(1);
    });
}

module.exports = { createTestUser, TEST_USER };