/**
 * Test authentication directly via API
 */
const axios = require('axios');

const testCredentials = {
  email: 'selenium.test@example.com',
  password: 'SeleniumTest123!'
};

async function testAuth() {
  console.log('🔐 Testing Authentication');
  console.log('═'.repeat(50));
  console.log(`Email: ${testCredentials.email}`);
  console.log(`Password: ${testCredentials.password}`);
  console.log('═'.repeat(50));
  
  try {
    // Test backend directly
    console.log('\n1️⃣ Testing Backend API directly...');
    const backendResponse = await axios.post('http://localhost:8001/api/v1/auth/login', {
      email: testCredentials.email,
      password: testCredentials.password
    });
    
    console.log('✅ Backend login successful!');
    console.log(`Token: ${backendResponse.data.access_token.substring(0, 50)}...`);
    
  } catch (error) {
    console.error('❌ Backend login failed:', error.response?.data || error.message);
  }
  
  try {
    // Test via frontend API service
    console.log('\n2️⃣ Testing via Frontend API service...');
    
    // Check what the frontend expects
    console.log('\nChecking frontend login format...');
    
    // Try different formats
    const formats = [
      { email: testCredentials.email, password: testCredentials.password },
      { username: testCredentials.email, password: testCredentials.password },
      { identifier: testCredentials.email, password: testCredentials.password }
    ];
    
    for (const format of formats) {
      console.log(`\nTrying format: ${JSON.stringify(Object.keys(format))}`);
      try {
        const response = await axios.post('http://localhost:3000/api/v1/auth/login', format);
        console.log('✅ Format worked!');
        break;
      } catch (e) {
        console.log(`❌ Format failed: ${e.response?.status || e.message}`);
      }
    }
    
  } catch (error) {
    console.error('Frontend API test error:', error.message);
  }
}

testAuth().catch(console.error);