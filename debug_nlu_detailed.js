// Debug script to understand NLU priority logic
const intentPatterns = new Map();

// Add all patterns
intentPatterns.set('add_to_plan', [
  /\b(add|include|put|save)\s+(this|that|it|the)?\s*(flight|hotel|activity)?\s*(to|in)?\s*(my\s+)?(plan|trip)\b/i,
  /\b(I'll take|select|choose|want)\s+(this|that|it)\b/i,
  /\badd\s+to\s+(my\s+)?(itinerary|trip)\b/i,
  /\bsave\s+for\s+later\b/i,
  /\badd\s+(this|that|the)\s+(flight|hotel|activity)\s+to\s+my\s+(plan|trip|itinerary)\b/i
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
        
        console.log(`  ${intentType}: pattern matched, confidence=${confidence}, adjusted=${adjustedConfidence}`);
        
        if (adjustedConfidence > highestConfidence) {
          highestConfidence = adjustedConfidence;
          detectedIntent = intentType;
        }
      }
      pattern.lastIndex = 0;
    }
  }
  
  // Default to search_flight if no clear intent but mentions travel-related keywords
  if (!detectedIntent && /\b(travel|vacation|holiday|visit)\b/i.test(message)) {
    detectedIntent = 'search_flight';
    highestConfidence = 0.3;
    console.log(`  fallback to search_flight: confidence=0.3`);
  }
  
  return {
    type: detectedIntent || 'search_flight',
    confidence: highestConfidence || 0.6
  };
}

// Test specific case
const testMessage = 'Add this to my plan';
console.log(`Testing: "${testMessage}"`);
const result = extractIntent(testMessage);
console.log(`Result: ${JSON.stringify(result)}`);