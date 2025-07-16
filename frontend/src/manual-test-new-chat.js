// Manual test script to verify new chat functionality
// Run this in the browser console

async function testNewChat() {
  console.log('Testing New Chat functionality...');
  
  // First, let's check the current session
  const currentSessionId = localStorage.getItem('currentSessionId');
  console.log('Current session ID:', currentSessionId);
  
  // Try to create a new session via API
  const response = await fetch('http://localhost:8001/api/v1/travel/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: 'Hello, I want to plan a trip',
      source: 'web'
    })
  });
  
  const data = await response.json();
  console.log('Create session response:', data);
  
  if (data.success) {
    console.log('✓ New session created:', data.data.session_id);
    console.log('✓ Initial response:', data.data.initial_response);
    console.log('✓ Metadata:', data.data.metadata);
    
    // Check if we can get the session
    const getResponse = await fetch(`http://localhost:8001/api/v1/travel/sessions/${data.data.session_id}`);
    const sessionData = await getResponse.json();
    console.log('Get session response:', sessionData);
    
    if (sessionData.success && sessionData.data.session_data) {
      console.log('✓ Conversation history:', sessionData.data.session_data.conversation_history);
    }
  } else {
    console.error('✗ Failed to create session:', data);
  }
}

// Run the test
testNewChat();