// Simple debug script to test NLU engine
const fs = require('fs');
const path = require('path');

// Read the TypeScript file and do basic testing
const nluCode = `
const intentPatterns = new Map();

// Add patterns
intentPatterns.set('add_to_plan', [
  /\\b(add|include|put|save)\\s+(this|that|it|the)?\\s*(flight|hotel|activity)?\\s*(to|in)?\\s*(my\\s+)?(plan|trip)\\b/i,
  /\\b(I'll take|select|choose|want)\\s+(this|that|it)\\b/i,
  /\\badd\\s+to\\s+(my\\s+)?(itinerary|trip)\\b/i,
  /\\bsave\\s+for\\s+later\\b/i,
  /\\badd\\s+(this|that|the)\\s+(flight|hotel|activity)\\s+to\\s+my\\s+(plan|trip|itinerary)\\b/i
]);

intentPatterns.set('book_item', [
  /\\b(book|reserve|confirm|finalize|purchase)\\s+(this|that|it|these)\\s*(now|tickets)?\\b/i,
  /\\bproceed\\s+with\\s+(booking|reservation)\\b/i,
  /\\bconfirm\\s+(my\\s+)?(booking|reservation)\\b/i,
  /\\b(I'm\\s+)?ready\\s+to\\s+book\\b/i,
  /\\bpurchase\\s+these\\s+tickets\\b/i,
  /\\bbook\\s+this\\s+now\\b/i
]);

function testPattern(message, intentType) {
  const patterns = intentPatterns.get(intentType);
  if (!patterns) return false;
  
  const normalizedMessage = message.toLowerCase();
  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    if (pattern.test(normalizedMessage)) {
      return true;
    }
  }
  return false;
}

// Test cases
const testCases = [
  {message: 'Add this to my plan', expected: 'add_to_plan'},
  {message: 'Book this now', expected: 'book_item'},
  {message: "I'm ready to book", expected: 'book_item'},
  {message: 'Add to my trip', expected: 'add_to_plan'}
];

testCases.forEach(testCase => {
  const result = testPattern(testCase.message, testCase.expected);
  console.log(\`\${testCase.message}: \${result ? 'MATCH' : 'NO MATCH'}\`);
});
`;

eval(nluCode);