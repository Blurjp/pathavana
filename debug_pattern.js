// Debug why "Save this for later" isn't matching

const pattern = /\bsave\s+for\s+later\b/i;
const message = "Save this for later";

console.log('Pattern:', pattern);
console.log('Message:', message);
console.log('Test result:', pattern.test(message));
console.log('Match result:', message.match(pattern));

// Test with normalized message
const normalizedMessage = message.toLowerCase();
console.log('Normalized:', normalizedMessage);
console.log('Normalized test:', pattern.test(normalizedMessage));
console.log('Normalized match:', normalizedMessage.match(pattern));