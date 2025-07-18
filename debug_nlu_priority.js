// Debug NLU priority and confidence issues

const intentPatterns = new Map();

// All patterns
intentPatterns.set('add_to_plan', [
  /\b(add|include|put|save)\s+(this|that|it|the)?\s*(flight|hotel|activity)?\s*(to|in)?\s*(my\s+)?(plan|trip)\b/i,
  /\b(I'll take|select|choose|want)\s+(this|that|it)\b/i,
  /\badd\s+to\s+(my\s+)?(itinerary|trip)\b/i,
  /\bsave\s+for\s+later\b/i,
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

function calculateConfidence(message, pattern) {
  pattern.lastIndex = 0;
  const match = message.match(pattern);
  if (!match) return 0;
  
  // Higher confidence for exact matches at the beginning of the message
  if (match.index === 0) return 0.9;
  
  // Medium confidence for matches in the middle
  if (match.index && match.index < message.length / 2) return 0.75;
  
  // Lower confidence for matches at the end
  return 0.6;
}

function extractIntent(message) {
  const normalizedMessage = message.toLowerCase();
  let highestConfidence = 0;
  let detectedIntent = null;
  let allMatches = [];
  
  const priorityOrder = ['add_to_plan', 'book_item', 'modify_plan', 'view_plan', 'check_budget', 'get_recommendations', 'search_flight', 'search_hotel'];
  
  // Check intents in priority order
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
  
  // Default fallback
  if (!detectedIntent && /\b(travel|vacation|holiday|visit)\b/i.test(message)) {
    detectedIntent = 'search_flight';
    highestConfidence = 0.3;
    allMatches.push({
      intent: 'search_flight',
      confidence: 0.3,
      adjusted: 0.3,
      pattern: 'fallback'
    });
  }
  
  return {
    type: detectedIntent || 'search_flight',
    confidence: highestConfidence || 0.6,
    allMatches: allMatches
  };
}

// Test the failing cases
const testCases = [
  'Add this to my plan',
  'What should I do in Tokyo?',
  'How much will this cost?',
  'Recommend restaurants in Paris',
  'Save this for later'
];

testCases.forEach(testCase => {
  console.log(`\nTesting: "${testCase}"`);
  const result = extractIntent(testCase);
  console.log(`Result: ${result.type} (confidence: ${result.confidence})`);
  console.log('All matches:', result.allMatches);
});