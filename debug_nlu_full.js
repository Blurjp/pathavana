// Debug NLU engine issues

const intentPatterns = new Map();

intentPatterns.set('add_to_plan', [
  /\b(add|include|put|save)\s+(this|that|it|the)?\s*(flight|hotel|activity)?\s*(to|in)?\s*(my\s+)?(plan|trip)\b/i,
  /\b(I'll take|select|choose|want)\s+(this|that|it)\b/i,
  /\badd\s+to\s+(my\s+)?(itinerary|trip)\b/i,
  /\bsave\s+(this|that|it)?\s*(for\s+)?later\b/i,
  /\badd\s+(this|that|the)\s+(flight|hotel|activity)\s+to\s+my\s+(plan|trip|itinerary)\b/i
]);

intentPatterns.set('get_recommendations', [
  /\b(recommend|suggest|what should|where should)\b/i,
  /\b(best|top|popular)\s+(places|things|activities|restaurants)\b/i,
  /\bwhat\s+(to\s+do|can\s+I\s+do|is\s+there\s+to\s+do)\b/i,
  /\bwhat\s+should\s+I\s+do\s+in\b/i,
  /\bmust[- ]see\b/i
]);

intentPatterns.set('check_budget', [
  /\b(budget|cost|price|how\s+much|total|expense)\b/i,
  /\bhow\s+much\s+will\s+this\s+cost\b/i,
  /\bcan\s+I\s+afford\b/i,
  /\bwithin\s+my\s+budget\b/i,
  /\bspending\s+so\s+far\b/i
]);

intentPatterns.set('search_flight', [
  /\b(find|search|look for|show me|get me|find me)\s+(a\s+)?flights?\b/i,
  /\bbook\s+(a\s+)?flights?\b/i,
  /\bfly(ing)?\s+(to|from)\b/i,
  /\bflight\s+(to|from|between)\b/i,
  /\bairfare\s+(to|from)\b/i,
  /\bwant\s+to\s+fly\b/i,
  /\bbook\s+(a\s+)?flight\s+(to|from)\b/i
]);

function calculateConfidence(message, pattern) {
  pattern.lastIndex = 0;
  const match = message.match(pattern);
  if (!match) return 0;
  
  if (match.index === 0) return 0.9;
  if (match.index && match.index < message.length / 2) return 0.75;
  return 0.6;
}

function extractIntent(message) {
  const normalizedMessage = message.toLowerCase();
  let highestConfidence = 0;
  let detectedIntent = null;
  let allMatches = [];
  
  const priorityOrder = ['add_to_plan', 'book_item', 'modify_plan', 'view_plan', 'check_budget', 'get_recommendations', 'search_flight', 'search_hotel'];
  
  for (const intentType of priorityOrder) {
    const patterns = intentPatterns.get(intentType);
    if (!patterns) continue;
    
    for (const pattern of patterns) {
      pattern.lastIndex = 0;
      if (pattern.test(normalizedMessage)) {
        const confidence = calculateConfidence(normalizedMessage, pattern);
        const adjustedConfidence = intentType === 'add_to_plan' || intentType === 'book_item' ? confidence + 0.1 : confidence;
        
        allMatches.push({
          intent: intentType,
          confidence: confidence,
          adjusted: adjustedConfidence,
          pattern: pattern.source
        });
        
        if (adjustedConfidence > highestConfidence) {
          highestConfidence = adjustedConfidence;
          detectedIntent = intentType;
        }
      }
      pattern.lastIndex = 0;
    }
  }
  
  if (!detectedIntent && /\b(travel|vacation|holiday|visit)\b/i.test(message)) {
    detectedIntent = 'search_flight';
    highestConfidence = 0.3;
  }
  
  return {
    type: detectedIntent || 'search_flight',
    confidence: highestConfidence || 0.6,
    allMatches: allMatches
  };
}

// Test the failing cases
const testCases = [
  'Save this for later',
  'What should I do in Tokyo?',
  'How much will this cost?',
  'Find flights to Tokyo for 2 people'
];

testCases.forEach(testCase => {
  console.log(`\nTesting: "${testCase}"`);
  const result = extractIntent(testCase);
  console.log(`Result: ${result.type} (confidence: ${result.confidence})`);
  console.log('All matches:', result.allMatches);
});