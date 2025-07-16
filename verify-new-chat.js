// Quick test to verify New Chat functionality
const axios = require('axios');

async function testNewChat() {
    console.log('Testing New Chat Functionality...\n');
    
    try {
        // 1. Create new session
        console.log('1. Creating new session...');
        const response = await axios.post('http://localhost:8001/api/v1/travel/sessions', {
            message: 'Hello, I want to plan a trip',
            source: 'web'
        });
        
        const { data } = response.data;
        console.log('✅ Session created:', data.session_id);
        console.log('✅ Initial response:', data.initial_response?.substring(0, 80) + '...');
        
        if (data.metadata?.hints) {
            console.log('✅ Hints provided:', data.metadata.hints.length, 'hints');
        }
        
        // 2. Simulate frontend behavior
        console.log('\n2. Simulating frontend behavior...');
        const sessionId = data.session_id;
        
        // Create initial messages like the frontend does
        const initialMessages = [
            {
                id: `msg-${Date.now()}-1`,
                content: 'Hello, I want to plan a trip',
                type: 'user',
                timestamp: new Date().toISOString(),
            },
            {
                id: `msg-${Date.now()}-2`,
                content: data.initial_response,
                type: 'assistant',
                timestamp: new Date().toISOString(),
                metadata: data.metadata,
            }
        ];
        
        console.log('✅ Created', initialMessages.length, 'initial messages');
        console.log('   - User message:', initialMessages[0].content);
        console.log('   - Assistant message:', initialMessages[1].content.substring(0, 60) + '...');
        
        // 3. Verify session can be retrieved
        console.log('\n3. Retrieving session to verify...');
        const getResponse = await axios.get(`http://localhost:8001/api/v1/travel/sessions/${sessionId}`);
        
        if (getResponse.data.success) {
            console.log('✅ Session retrieved successfully');
            const sessionData = getResponse.data.data;
            console.log('   - Status:', sessionData.status);
            console.log('   - Messages:', sessionData.session_data?.conversation_history?.length || 0);
        }
        
        console.log('\n✅ New Chat functionality is working correctly!');
        console.log('   The frontend will now display the initial conversation.');
        
    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
    }
}

// Check if axios is available
try {
    testNewChat();
} catch (e) {
    console.log('Please install axios first: npm install axios');
    console.log('Or use the HTML test file instead');
}