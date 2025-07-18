const { TravelNLUEngine } = require('./frontend/src/services/NLUEngine.ts');

// Test what's happening in the actual test
const nluEngine = new TravelNLUEngine();

const testCases = [
  'Save this for later',
  'What should I do in Tokyo?',
  'How much will this cost?'
];

testCases.forEach(testCase => {
  console.log(`\nTesting: "${testCase}"`);
  try {
    const result = nluEngine.extractIntent(testCase);
    console.log(`Result: ${result.type} (confidence: ${result.confidence})`);
  } catch (error) {
    console.error('Error:', error.message);
  }
});