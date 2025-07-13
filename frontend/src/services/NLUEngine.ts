import {
  NLUEngine,
  Intent,
  Entity,
  EnhancedChatMessage,
  ConversationContext,
  ClarificationRequest,
  ConversationState
} from '../types/AIAgentTypes';

export class TravelNLUEngine implements NLUEngine {
  private intentPatterns: Map<string, RegExp[]>;
  private entityPatterns: Map<string, RegExp[]>;

  constructor() {
    this.intentPatterns = this.initializeIntentPatterns();
    this.entityPatterns = this.initializeEntityPatterns();
  }

  private initializeIntentPatterns(): Map<string, RegExp[]> {
    const patterns = new Map<string, RegExp[]>();
    
    patterns.set('search_flight', [
      /\b(find|search|look for|show me|book|get me|find me)\s+(a\s+)?flights?\b/i,
      /\bfly(ing)?\s+(to|from)\b/i,
      /\bflight\s+(to|from|between)\b/i,
      /\bairfare\s+(to|from)\b/i,
      /\bwant\s+to\s+fly\b/i
    ]);

    patterns.set('search_hotel', [
      /\b(find|search|look for|show me|book|get me)\s+(a\s+)?hotels?\b/i,
      /\b(stay|accommodation|lodging|where to stay)\b/i,
      /\bhotel\s+(in|near|at)\b/i,
      /\bneed\s+(a\s+)?place\s+to\s+stay\b/i
    ]);

    patterns.set('add_to_plan', [
      /\b(add|include|put|save)\s+(this|that|it)?\s*(to|in)?\s*(my\s+)?plan\b/i,
      /\b(I'll take|select|choose|want)\s+(this|that|it)\b/i,
      /\badd\s+to\s+(my\s+)?itinerary\b/i,
      /\bsave\s+for\s+later\b/i
    ]);

    patterns.set('view_plan', [
      /\b(show|view|see|display|check)\s+(me\s+)?(my\s+)?(travel\s+)?plan\b/i,
      /\bwhat's\s+in\s+my\s+(plan|itinerary)\b/i,
      /\bmy\s+trip\s+so\s+far\b/i,
      /\bcurrent\s+(plan|itinerary)\b/i
    ]);

    patterns.set('modify_plan', [
      /\b(change|modify|update|edit|remove|delete)\s+.*(plan|itinerary|booking)\b/i,
      /\bcancel\s+(this|that|the)\b/i,
      /\breplace\s+.*(with)\b/i,
      /\bswitch\s+(to|from)\b/i
    ]);

    patterns.set('book_item', [
      /\b(book|reserve|confirm|finalize|purchase)\s+(this|that|it|now)\b/i,
      /\bproceed\s+with\s+(booking|reservation)\b/i,
      /\bconfirm\s+(my\s+)?(booking|reservation)\b/i,
      /\bready\s+to\s+book\b/i
    ]);

    patterns.set('get_recommendations', [
      /\b(recommend|suggest|what should|where should)\b/i,
      /\b(best|top|popular)\s+(places|things|activities|restaurants)\b/i,
      /\bwhat\s+(to do|can I do|is there to do)\b/i,
      /\bmust[- ]see\b/i
    ]);

    patterns.set('check_budget', [
      /\b(budget|cost|price|how much|total|expense)\b/i,
      /\bcan\s+I\s+afford\b/i,
      /\bwithin\s+my\s+budget\b/i,
      /\bspending\s+so\s+far\b/i
    ]);

    return patterns;
  }

  private initializeEntityPatterns(): Map<string, RegExp[]> {
    const patterns = new Map<string, RegExp[]>();
    
    patterns.set('destination', [
      /\bto\s+([A-Z][a-zA-Z\s-]+?)(?:\s+(?:and|,|\.|$))/gi,
      /\bin\s+([A-Z][a-zA-Z\s-]+?)(?:\s+(?:and|,|\.|$))/gi,
      /\bvisit\s+([A-Z][a-zA-Z\s-]+?)(?:\s+(?:and|,|\.|$))/gi,
      /\bgoing\s+to\s+([A-Z][a-zA-Z\s-]+?)(?:\s+(?:and|,|\.|$))/gi,
      /\b([A-Z][a-zA-Z\s-]+?)\s+(?:trip|vacation|holiday)/gi
    ]);

    patterns.set('date', [
      /\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b/g,
      /\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(,?\s+\d{4})?\b/gi,
      /\b(tomorrow|today|next\s+week|next\s+month|this\s+weekend)\b/gi,
      /\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/gi,
      /\breturning\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})/gi
    ]);

    patterns.set('budget', [
      /\$?([\d,]+)(\.\d{2})?\s*(?:dollars?|usd)?/gi,
      /\bbudget\s+(?:of\s+)?(\$?[\d,]+)/gi,
      /\bunder\s+(\$?[\d,]+)/gi,
      /\baround\s+(\$?[\d,]+)/gi
    ]);

    patterns.set('travelers', [
      /\b(\d+)\s+(?:people|persons?|adults?|children|kids?|infants?|travelers?)\b/gi,
      /\bparty\s+of\s+(\d+)\b/gi,
      /\bfor\s+(\d+)\s+(?:people|person)\b/gi,
      /\b(solo|alone|myself|couple|family)\b/gi
    ]);

    patterns.set('preference', [
      /\b(luxury|budget|cheap|expensive|direct|nonstop|window|aisle)\b/gi,
      /\b(first class|business class|economy|premium economy)\b/gi,
      /\b(pet[- ]friendly|family[- ]friendly|adults?[- ]only)\b/gi,
      /\b(beach|mountain|city|rural|downtown|airport)\b/gi
    ]);

    return patterns;
  }

  extractIntent(message: string): Intent {
    const normalizedMessage = message.toLowerCase();
    let highestConfidence = 0;
    let detectedIntent: string | null = null;
    const parameters: Record<string, any> = {};

    // Check each intent pattern
    for (const [intentType, patterns] of this.intentPatterns) {
      for (const pattern of patterns) {
        // Reset regex lastIndex
        pattern.lastIndex = 0;
        if (pattern.test(normalizedMessage)) {
          const confidence = this.calculateConfidence(normalizedMessage, pattern);
          if (confidence > highestConfidence) {
            highestConfidence = confidence;
            detectedIntent = intentType;
          }
        }
        // Reset again for next test
        pattern.lastIndex = 0;
      }
    }

    // Default to search_flight if no clear intent but mentions travel-related keywords
    if (!detectedIntent && /\b(travel|trip|vacation|holiday|visit)\b/i.test(message)) {
      detectedIntent = 'search_flight';
      highestConfidence = 0.3;
    }

    return {
      type: (detectedIntent || 'search_flight') as any,
      confidence: highestConfidence || 0.5,
      parameters
    };
  }

  extractEntities(message: string): Entity[] {
    const entities: Entity[] = [];
    
    for (const [entityType, patterns] of this.entityPatterns) {
      for (const pattern of patterns) {
        // Reset the regex lastIndex to ensure we start from the beginning
        pattern.lastIndex = 0;
        const matches = message.matchAll(new RegExp(pattern.source, pattern.flags));
        
        for (const match of matches) {
          // For dates, we might have multiple capture groups
          let capturedValue = match[1];
          if (entityType === 'date' && match[2]) {
            capturedValue = `${match[1]} ${match[2]}`;
          }
          if (entityType === 'date' && match[3]) {
            capturedValue = `${capturedValue}${match[3]}`;
          }
          
          if (capturedValue || match[0]) {
            const rawValue = capturedValue || match[0];
            const value = this.normalizeEntityValue(entityType, rawValue);
            if (value !== null && value !== undefined) {
              entities.push({
                type: entityType as any,
                value,
                confidence: 0.8,
                position: [match.index || 0, (match.index || 0) + match[0].length]
              });
            }
          }
        }
      }
    }

    return this.deduplicateEntities(entities);
  }

  maintainContext(messages: EnhancedChatMessage[]): ConversationContext {
    const context: ConversationContext = {
      state: this.determineConversationState(messages),
      entities: this.accumulateEntities(messages),
      missingFields: this.identifyMissingFields(messages),
      lastIntent: messages.length > 0 ? messages[messages.length - 1].metadata.intent || null : null,
      clarificationNeeded: false
    };

    // Check if clarification is needed based on ambiguous entities or missing required fields
    if (context.missingFields.length > 0 || this.hasAmbiguousEntities(context.entities)) {
      context.clarificationNeeded = true;
    }

    return context;
  }

  clarifyIntent(message: string, context: ConversationContext): ClarificationRequest {
    const missingFields = context.missingFields;
    
    if (missingFields.includes('destination')) {
      return {
        question: "Where would you like to travel to?",
        type: 'open_ended'
      };
    }
    
    if (missingFields.includes('dates')) {
      return {
        question: "When would you like to travel?",
        type: 'open_ended'
      };
    }
    
    if (missingFields.includes('travelers')) {
      return {
        question: "How many people will be traveling?",
        options: ['1', '2', '3-4', '5+'],
        type: 'single_choice'
      };
    }

    // Check for ambiguous destinations
    const destinations = context.entities.filter(e => e.type === 'destination');
    if (destinations.length > 1) {
      return {
        question: "I found multiple destinations. Which one is your primary destination?",
        options: destinations.map(d => d.value as string),
        type: 'single_choice'
      };
    }

    return {
      question: "Could you provide more details about your travel plans?",
      type: 'open_ended'
    };
  }

  private calculateConfidence(message: string, pattern: RegExp): number {
    // Simple confidence calculation based on pattern match strength
    const match = message.match(pattern);
    if (!match) return 0;
    
    // Higher confidence for exact matches at the beginning of the message
    if (match.index === 0) return 0.9;
    
    // Medium confidence for matches in the middle
    if (match.index && match.index < message.length / 2) return 0.7;
    
    // Lower confidence for matches at the end
    return 0.5;
  }

  private normalizeEntityValue(entityType: string, value: string): any {
    switch (entityType) {
      case 'destination':
        return value.trim().replace(/\s+/g, ' ').replace(/[,\.]/g, '');
      
      case 'date':
        // Simple date normalization - in production, use a proper date parser
        return value.trim();
      
      case 'budget':
        // Extract numeric value, handle various formats
        const cleanValue = value.replace(/[\$,]/g, '');
        const budgetMatch = cleanValue.match(/(\d+(?:\.\d{2})?)/);
        return budgetMatch ? parseFloat(budgetMatch[1]) : null;
      
      case 'travelers':
        // Extract numeric value or interpret text
        const numberMatch = value.match(/\d+/);
        if (numberMatch) return parseInt(numberMatch[0]);
        if (/solo|alone|myself/.test(value.toLowerCase())) return 1;
        if (/couple/.test(value.toLowerCase())) return 2;
        if (/family/.test(value.toLowerCase())) return 4;
        return null;
      
      case 'preference':
        return value.toLowerCase().trim();
      
      default:
        return value;
    }
  }

  private deduplicateEntities(entities: Entity[]): Entity[] {
    const seen = new Set<string>();
    return entities.filter(entity => {
      const key = `${entity.type}:${entity.value}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  private determineConversationState(messages: EnhancedChatMessage[]): ConversationState {
    if (messages.length === 0) return ConversationState.GREETING;
    
    const lastMessage = messages[messages.length - 1];
    const lastIntent = lastMessage.metadata.intent?.type;
    
    // Determine state based on last intent and conversation history
    if (lastIntent === 'search_flight' || lastIntent === 'search_hotel') {
      return ConversationState.SEARCHING;
    }
    
    if (lastIntent === 'add_to_plan') {
      return ConversationState.ADDING_TO_PLAN;
    }
    
    if (lastIntent === 'view_plan') {
      return ConversationState.REVIEWING_PLAN;
    }
    
    if (lastIntent === 'book_item') {
      return ConversationState.BOOKING;
    }
    
    // Check if we have search results in recent messages
    const hasSearchResults = messages.slice(-3).some(msg => 
      msg.metadata.attachments?.some(att => att.type === 'search_results')
    );
    
    if (hasSearchResults) {
      return ConversationState.PRESENTING_OPTIONS;
    }
    
    // Default to gathering requirements if we don't have enough information
    return ConversationState.GATHERING_REQUIREMENTS;
  }

  private accumulateEntities(messages: EnhancedChatMessage[]): Entity[] {
    const allEntities: Entity[] = [];
    
    // Accumulate entities from all messages, prioritizing more recent ones
    for (let i = messages.length - 1; i >= 0; i--) {
      const messageEntities = messages[i].metadata.entities || [];
      allEntities.push(...messageEntities);
    }
    
    return this.deduplicateEntities(allEntities);
  }

  private identifyMissingFields(messages: EnhancedChatMessage[]): string[] {
    const entities = this.accumulateEntities(messages);
    const missingFields: string[] = [];
    
    // Check for required fields based on the last intent
    const lastIntent = messages[messages.length - 1]?.metadata.intent?.type;
    
    if (lastIntent === 'search_flight') {
      if (!entities.some(e => e.type === 'destination')) {
        missingFields.push('destination');
      }
      if (!entities.some(e => e.type === 'date')) {
        missingFields.push('dates');
      }
    }
    
    if (lastIntent === 'search_hotel') {
      if (!entities.some(e => e.type === 'destination')) {
        missingFields.push('destination');
      }
      if (!entities.some(e => e.type === 'date')) {
        missingFields.push('check-in dates');
      }
    }
    
    // Always check for number of travelers if not specified
    if (!entities.some(e => e.type === 'travelers')) {
      missingFields.push('travelers');
    }
    
    return missingFields;
  }

  private hasAmbiguousEntities(entities: Entity[]): boolean {
    // Check for multiple destinations
    const destinations = entities.filter(e => e.type === 'destination');
    if (destinations.length > 1) return true;
    
    // Check for conflicting dates
    const dates = entities.filter(e => e.type === 'date');
    if (dates.length > 2) return true; // More than departure and return
    
    // Check for low confidence entities
    return entities.some(e => e.confidence < 0.5);
  }
}