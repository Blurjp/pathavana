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
      /\b(find|search|look for|show me|get me|find me)\s+(a\s+)?flights?\b/i,
      /\bbook\s+(a\s+)?flights?\b/i,
      /\bfly(ing)?\s+(to|from)\b/i,
      /\bflight\s+(to|from|between)\b/i,
      /\bairfare\s+(to|from)\b/i,
      /\bwant\s+to\s+fly\b/i,
      /\bbook\s+(a\s+)?flight\s+(to|from)\b/i
    ]);

    patterns.set('search_hotel', [
      /\b(find|search|look for|show me|get me)\s+(a\s+)?hotels?\b/i,
      /\bbook\s+(a\s+)?hotels?\b/i,
      /\b(stay|accommodation|lodging|where to stay)\b/i,
      /\bhotel\s+(in|near|at)\b/i,
      /\bneed\s+(a\s+)?place\s+to\s+stay\b/i,
      /\bbook\s+(a\s+)?hotel\s+(in|near|at|for)\b/i
    ]);

    patterns.set('add_to_plan', [
      /\b(add|include|put|save)\s+(this|that|it|the)?\s*(flight|hotel|activity)?\s*(to|in)?\s*(my\s+)?(plan|trip|itinerary)\b/i,
      /\b(I'll take|select|choose|want)\s+(this|that|it)\b/i,
      /\badd\s+to\s+(my\s+)?(itinerary|trip)\b/i,
      /\bsave\s+(this|that|it)?\s*(for\s+)?later\b/i,
      /\badd\s+(this|that|the)\s+(flight|hotel|activity)\s+to\s+my\s+(plan|trip|itinerary)\b/i
    ]);

    patterns.set('view_plan', [
      /\b(show|view|see|display|check)\s+(me\s+)?(my\s+)?(travel\s+)?plan\b/i,
      /\bwhat('s|\s+is)\s+in\s+my\s+(plan|itinerary)\b/i,
      /\b(my\s+)?trip\s+so\s+far\b/i,
      /\b(view|check|display)\s+(my\s+)?current\s+(plan|itinerary)\b/i,
      /\b(display|show)\s+(my\s+)?bookings?\b/i
    ]);

    patterns.set('modify_plan', [
      /\b(change|modify|update|edit|remove|delete)\s+.*(plan|itinerary|booking)\b/i,
      /\bcancel\s+(this|that|the)\b/i,
      /\breplace\s+.*(with)\b/i,
      /\bswitch\s+(to|from)\b/i
    ]);

    patterns.set('book_item', [
      /\b(book|reserve|confirm|finalize|purchase)\s+(this|that|it|these)\s*(now|tickets)?\b/i,
      /\bproceed\s+with\s+(booking|reservation)\b/i,
      /\bconfirm\s+(my\s+)?(booking|reservation)\b/i,
      /\b(I'm\s+)?ready\s+to\s+book\b/i,
      /\bpurchase\s+these\s+tickets\b/i,
      /\bbook\s+this\s+now\b/i
    ]);

    patterns.set('get_recommendations', [
      /\b(recommend|suggest|what should|where should)\b/i,
      /\b(best|top|popular)\s+(places|things|activities|restaurants)\b/i,
      /\bwhat\s+(to\s+do|can\s+I\s+do|is\s+there\s+to\s+do)\b/i,
      /\bwhat\s+should\s+I\s+do\s+in\b/i,
      /\bmust[- ]see\b/i,
      /\bwhat('s|\s+is)\s+popular\b/i
    ]);

    patterns.set('check_budget', [
      /\b(budget|cost|price|how\s+much|total|expenses?)\b/i,
      /\bhow\s+much\s+will\s+this\s+cost\b/i,
      /\bcan\s+I\s+afford\b/i,
      /\bwithin\s+my\s+budget\b/i,
      /\bspending\s+so\s+far\b/i
    ]);

    return patterns;
  }

  private initializeEntityPatterns(): Map<string, RegExp[]> {
    const patterns = new Map<string, RegExp[]>();
    
    patterns.set('destination', [
      /(?:fly|travel|go)\s+to\s+([A-Z][a-zA-Z\s-]+?)(?=\s+(?:for|on|in|and|,|\.|$))/gi,
      /\bflights?\s+to\s+([A-Z][a-zA-Z\s-]+?)(?=\s+(?:for|on|in|and|,|\.|$))/gi,
      /\bvisit\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)(?=\s+|$)/gi,
      /\bin\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)(?=\s+(?:for|on|and|,|\.|$))/gi,
      /\bgoing\s+to\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)(?=\s+(?:for|on|and|,|\.|$))/gi,
      /\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:trip|vacation|holiday)/gi,
      /\b([A-Z][a-zA-Z]+)\s+to\s+([A-Z][a-zA-Z]+)/g,
      /\b(?:flying|traveling)\s+to\s+([A-Z][a-zA-Z]+)/gi
    ]);

    patterns.set('date', [
      /\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b/g,
      /\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(,?\s+\d{4})?\b/gi,
      /\b(tomorrow|today|next\s+week|next\s+month|this\s+weekend)\b/gi,
      /\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/gi,
      /\bon\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})/gi,
      /\breturning\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})/gi,
      /\b(march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b/gi
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


    // Priority order for intent checking (more specific first)
    const priorityOrder = ['add_to_plan', 'book_item', 'modify_plan', 'view_plan', 'check_budget', 'get_recommendations', 'search_flight', 'search_hotel'];
    
    // Check intents in priority order
    for (const intentType of priorityOrder) {
      const patterns = this.intentPatterns.get(intentType);
      if (!patterns) continue;
      
      for (const pattern of patterns) {
        // Reset regex lastIndex
        pattern.lastIndex = 0;
        if (pattern.test(normalizedMessage)) {
          const confidence = this.calculateConfidence(normalizedMessage, pattern);
          // Give bonus confidence to more specific intents
          const adjustedConfidence = intentType === 'add_to_plan' || intentType === 'book_item' ? confidence + 0.1 : confidence;
          
          
          if (adjustedConfidence > highestConfidence) {
            highestConfidence = adjustedConfidence;
            detectedIntent = intentType;
          }
        }
        // Reset again for next test
        pattern.lastIndex = 0;
      }
    }

    // Default to search_flight if no clear intent but mentions travel-related keywords
    if (!detectedIntent && /\b(travel|vacation|holiday|visit)\b/i.test(message)) {
      detectedIntent = 'search_flight';
      highestConfidence = 0.3;
    }
    
    
    return {
      type: (detectedIntent || 'search_flight') as any,
      confidence: highestConfidence || 0.6,
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
          // Handle different capture group scenarios
          if (entityType === 'destination' && match[1] && match[2]) {
            // Pattern with two capture groups (e.g., "Tokyo to Kyoto")
            const firstDestination = this.normalizeEntityValue(entityType, match[1]);
            const secondDestination = this.normalizeEntityValue(entityType, match[2]);
            
            if (firstDestination !== null && firstDestination !== undefined) {
              const entity1: Entity = {
                type: entityType as any,
                value: firstDestination,
                confidence: 0.8,
                position: [match.index || 0, (match.index || 0) + match[1].length] as [number, number]
              };
              
              
              entities.push(entity1);
            }
            
            if (secondDestination !== null && secondDestination !== undefined) {
              const secondStart = (match.index || 0) + match[0].indexOf(match[2]);
              const entity2: Entity = {
                type: entityType as any,
                value: secondDestination,
                confidence: 0.8,
                position: [secondStart, secondStart + match[2].length] as [number, number]
              };
              
              
              entities.push(entity2);
            }
          } else {
            // Standard single capture group or date handling
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
                const entity: Entity = {
                  type: entityType as any,
                  value,
                  confidence: 0.8,
                  position: [match.index || 0, (match.index || 0) + match[0].length] as [number, number]
                };
                
                
                entities.push(entity);
              }
            }
          }
        }
      }
    }

    const deduplicated = this.deduplicateEntities(entities);
    
    
    return deduplicated;
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
    const result: Entity[] = [];
    
    for (const entity of entities) {
      let shouldAdd = true;
      
      // Check against existing entities
      for (let i = 0; i < result.length; i++) {
        const existing = result[i];
        
        // If same type and value, skip
        if (existing.type === entity.type && existing.value === entity.value) {
          shouldAdd = false;
          break;
        }
        
        // If same type and overlapping positions, keep the more specific one
        if (existing.type === entity.type) {
          const existingStart = existing.position[0];
          const existingEnd = existing.position[1];
          const entityStart = entity.position[0];
          const entityEnd = entity.position[1];
          
          // Check if they overlap
          if (!(entityEnd <= existingStart || entityStart >= existingEnd)) {
            // They overlap, keep the more specific (longer) one
            if (entityEnd - entityStart > existingEnd - existingStart) {
              // New entity is more specific, replace the existing one
              result[i] = entity;
              shouldAdd = false;
              break;
            } else {
              // Existing entity is more specific, skip the new one
              shouldAdd = false;
              break;
            }
          }
        }
      }
      
      if (shouldAdd) {
        result.push(entity);
      }
    }
    
    return result;
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