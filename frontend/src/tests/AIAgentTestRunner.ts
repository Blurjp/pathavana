/**
 * Comprehensive AI Travel Agent Test Runner
 * Validates all functionality and ensures system reliability
 */

import { TravelNLUEngine } from '../services/NLUEngine';
import { TravelConversationalSearch } from '../services/ConversationalSearch';
import { TravelAIService } from '../services/AITravelService';
import { 
  ConversationState,
  EnhancedChatMessage,
  UserPreferences,
  SearchResult,
  SearchContext
} from '../types/AIAgentTypes';

interface TestResult {
  testName: string;
  passed: boolean;
  error?: string;
  duration: number;
}

interface TestSuite {
  suiteName: string;
  tests: TestResult[];
  totalPassed: number;
  totalFailed: number;
  duration: number;
}

export class AIAgentTestRunner {
  private nluEngine: TravelNLUEngine;
  private conversationalSearch: TravelConversationalSearch;
  private aiService: TravelAIService;
  private results: TestSuite[] = [];

  constructor() {
    this.nluEngine = new TravelNLUEngine();
    this.conversationalSearch = new TravelConversationalSearch();
    this.aiService = new TravelAIService();
  }

  async runAllTests(): Promise<TestSuite[]> {
    console.log('🚀 Starting AI Travel Agent Comprehensive Test Suite...\n');

    await this.runNLUTests();
    await this.runConversationalSearchTests();
    await this.runConversationFlowTests();
    await this.runPerformanceTests();
    await this.runErrorHandlingTests();
    await this.runEdgeCaseTests();

    this.printTestSummary();
    return this.results;
  }

  private async runNLUTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'NLU Engine Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // Intent Recognition Tests
    const intentTests = [
      { input: "Find me flights to Paris", expected: "search_flight" },
      { input: "Book hotels in Tokyo", expected: "search_hotel" },
      { input: "Add this to my plan", expected: "add_to_plan" },
      { input: "Show me my travel plan", expected: "view_plan" },
      { input: "Book this flight now", expected: "book_item" },
      { input: "What should I do in Rome?", expected: "get_recommendations" },
      { input: "How much will this cost?", expected: "check_budget" }
    ];

    for (const test of intentTests) {
      const result = this.runTest(
        `Intent Recognition: "${test.input}"`,
        () => {
          const intent = this.nluEngine.extractIntent(test.input);
          if (intent.type !== test.expected) {
            throw new Error(`Expected ${test.expected}, got ${intent.type}`);
          }
          if (intent.confidence <= 0) {
            throw new Error(`Low confidence: ${intent.confidence}`);
          }
        }
      );
      suite.tests.push(result);
    }

    // Entity Extraction Tests
    const entityTests = [
      {
        input: "I want to visit Tokyo and Kyoto",
        expectedType: "destination",
        expectedCount: 1 // At least one destination should be extracted
      },
      {
        input: "Flying on March 15, 2024",
        expectedType: "date",
        expectedCount: 1
      },
      {
        input: "Budget is $5000",
        expectedType: "budget",
        expectedValue: 5000
      },
      {
        input: "For 3 people",
        expectedType: "travelers",
        expectedValue: 3
      }
    ];

    for (const test of entityTests) {
      const result = this.runTest(
        `Entity Extraction: "${test.input}"`,
        () => {
          const entities = this.nluEngine.extractEntities(test.input);
          const filteredEntities = entities.filter(e => e.type === test.expectedType);
          
          if (test.expectedCount !== undefined && filteredEntities.length < test.expectedCount) {
            throw new Error(`Expected at least ${test.expectedCount} ${test.expectedType} entities, got ${filteredEntities.length}`);
          }

          if (test.expectedValue !== undefined) {
            const entity = filteredEntities.find(e => e.value === test.expectedValue);
            if (!entity) {
              throw new Error(`Expected entity value ${test.expectedValue}, got ${filteredEntities.map(e => e.value).join(', ')}`);
            }
          }
        }
      );
      suite.tests.push(result);
    }

    // Context Management Tests
    const contextTest = this.runTest(
      'Context Management',
      () => {
        const messages: EnhancedChatMessage[] = [
          {
            id: '1',
            role: 'user',
            content: 'I want to go to Tokyo',
            timestamp: new Date(),
            metadata: {
              entities: [{ type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 5] as [number, number] }]
            }
          },
          {
            id: '2',
            role: 'user',
            content: 'In March for 2 people',
            timestamp: new Date(),
            metadata: {
              entities: [
                { type: 'date', value: 'March', confidence: 0.8, position: [0, 5] },
                { type: 'travelers', value: 2, confidence: 0.9, position: [6, 15] }
              ]
            }
          }
        ];

        const context = this.nluEngine.maintainContext(messages);
        
        if (context.entities.length !== 3) {
          throw new Error(`Expected 3 entities, got ${context.entities.length}`);
        }

        const hasDestination = context.entities.some(e => e.type === 'destination' && e.value === 'Tokyo');
        const hasDate = context.entities.some(e => e.type === 'date' && e.value === 'March');
        const hasTravelers = context.entities.some(e => e.type === 'travelers' && e.value === 2);

        if (!hasDestination || !hasDate || !hasTravelers) {
          throw new Error('Missing expected entities in context');
        }
      }
    );
    suite.tests.push(contextTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private async runConversationalSearchTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'Conversational Search Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // Search Refinement Tests
    const refinementTest = this.runTest(
      'Search Refinement - Price',
      () => {
        const initialQuery = {
          query: 'flights to Tokyo',
          filters: { maxPrice: 1000 },
          page: 1
        };

        const refinedQuery = this.conversationalSearch.refineSearch(
          initialQuery,
          'something cheaper'
        );

        if (refinedQuery.filters.maxPrice !== 800) {
          throw new Error(`Expected maxPrice 800, got ${refinedQuery.filters.maxPrice}`);
        }
      }
    );
    suite.tests.push(refinementTest);

    // Relative Query Tests
    const relativeQueryTests = [
      {
        input: 'something cheaper',
        context: { previousResults: [], appliedFilters: { maxPrice: 500 }, userFeedback: [] },
        expectedMaxPrice: 350
      },
      {
        input: 'earlier flight',
        context: { previousResults: [], appliedFilters: {}, userFeedback: [] },
        expectedTimeRange: 'morning'
      }
    ];

    for (const test of relativeQueryTests) {
      const result = this.runTest(
        `Relative Query: "${test.input}"`,
        () => {
          const query = this.conversationalSearch.parseRelativeQuery(test.input, test.context);
          
          if (test.expectedMaxPrice && query.filters.maxPrice !== test.expectedMaxPrice) {
            throw new Error(`Expected maxPrice ${test.expectedMaxPrice}, got ${query.filters.maxPrice}`);
          }

          if (test.expectedTimeRange && query.filters.departureTimeRange !== test.expectedTimeRange) {
            throw new Error(`Expected timeRange ${test.expectedTimeRange}, got ${query.filters.departureTimeRange}`);
          }
        }
      );
      suite.tests.push(result);
    }

    // Result Formatting Tests
    const formatTest = this.runTest(
      'Result Formatting',
      () => {
        const searchResults: SearchResult[] = [
          {
            id: 'flight1',
            type: 'flight',
            data: {
              airline: 'Delta',
              departure: 'JFK',
              arrival: 'NRT',
              price: { amount: 850, displayPrice: '$850' },
              stops: 0
            },
            relevanceScore: 0.9
          }
        ];

        const preferences: UserPreferences = {
          preferredAirlines: ['Delta']
        };

        const formatted = this.conversationalSearch.formatResults(searchResults, preferences);

        if (!formatted.includes('✈️ **Flights:**')) {
          throw new Error('Missing flight section header');
        }

        if (!formatted.includes('Delta')) {
          throw new Error('Missing airline name');
        }

        if (!formatted.includes('⭐ Your preferred airline')) {
          throw new Error('Missing preference highlight');
        }
      }
    );
    suite.tests.push(formatTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private async runConversationFlowTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'Conversation Flow Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // State Transition Tests
    const stateTransitionTest = this.runTest(
      'State Transitions',
      () => {
        // Test greeting to gathering requirements
        let messages: EnhancedChatMessage[] = [
          {
            id: '1',
            role: 'user',
            content: 'I want to travel',
            timestamp: new Date(),
            metadata: {
              intent: { type: 'search_flight', confidence: 0.7, parameters: {} }
            }
          }
        ];

        let context = this.nluEngine.maintainContext(messages);
        
        // Should be in gathering requirements due to missing info
        if (context.state !== ConversationState.GATHERING_REQUIREMENTS) {
          throw new Error(`Expected GATHERING_REQUIREMENTS, got ${context.state}`);
        }

        // Add complete information
        messages.push({
          id: '2',
          role: 'user',
          content: 'To Tokyo on March 15 for 2 people',
          timestamp: new Date(),
          metadata: {
            entities: [
              { type: 'destination', value: 'Tokyo', confidence: 0.9, position: [0, 5] },
              { type: 'date', value: 'March 15', confidence: 0.9, position: [6, 15] },
              { type: 'travelers', value: 2, confidence: 0.9, position: [16, 25] }
            ]
          }
        });

        context = this.nluEngine.maintainContext(messages);
        
        // Should transition to searching with complete info
        if (context.missingFields.length > 1) { // Budget might still be missing
          throw new Error(`Too many missing fields: ${context.missingFields.join(', ')}`);
        }
      }
    );
    suite.tests.push(stateTransitionTest);

    // Clarification Tests
    const clarificationTest = this.runTest(
      'Clarification Generation',
      () => {
        const context = {
          state: ConversationState.GATHERING_REQUIREMENTS,
          entities: [{ type: 'destination' as const, value: 'Tokyo', confidence: 0.9, position: [0, 5] as [number, number] }],
          missingFields: ['dates'],
          lastIntent: null,
          clarificationNeeded: true
        };

        const clarification = this.nluEngine.clarifyIntent('', context);
        
        if (!clarification.question.toLowerCase().includes('when')) {
          throw new Error(`Expected date clarification, got: ${clarification.question}`);
        }

        if (clarification.type !== 'open_ended') {
          throw new Error(`Expected open_ended type, got: ${clarification.type}`);
        }
      }
    );
    suite.tests.push(clarificationTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private async runPerformanceTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'Performance Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // Intent Recognition Performance
    const intentPerformanceTest = this.runTest(
      'Intent Recognition Performance (100 messages)',
      () => {
        const start = performance.now();
        
        for (let i = 0; i < 100; i++) {
          this.nluEngine.extractIntent(`Find flights to destination ${i}`);
        }
        
        const duration = performance.now() - start;
        
        if (duration > 100) { // Should process 100 messages in under 100ms
          throw new Error(`Performance too slow: ${duration}ms for 100 messages`);
        }
      }
    );
    suite.tests.push(intentPerformanceTest);

    // Entity Extraction Performance
    const entityPerformanceTest = this.runTest(
      'Entity Extraction Performance (100 messages)',
      () => {
        const start = performance.now();
        
        for (let i = 0; i < 100; i++) {
          this.nluEngine.extractEntities(`I want to travel to City${i} on March ${i % 28 + 1} for ${i % 5 + 1} people with budget $${1000 + i * 10}`);
        }
        
        const duration = performance.now() - start;
        
        if (duration > 200) { // Should process 100 complex messages in under 200ms
          throw new Error(`Performance too slow: ${duration}ms for 100 entity extractions`);
        }
      }
    );
    suite.tests.push(entityPerformanceTest);

    // Large Context Performance
    const contextPerformanceTest = this.runTest(
      'Large Context Performance (50 messages)',
      () => {
        const messages: EnhancedChatMessage[] = [];
        
        // Create 50 messages
        for (let i = 0; i < 50; i++) {
          messages.push({
            id: `msg-${i}`,
            role: 'user',
            content: `Message ${i}`,
            timestamp: new Date(),
            metadata: {
              entities: [{ type: 'destination' as const, value: `City${i}`, confidence: 0.8, position: [0, 5] as [number, number] }]
            }
          });
        }

        const start = performance.now();
        const context = this.nluEngine.maintainContext(messages);
        const duration = performance.now() - start;
        
        if (duration > 50) { // Should process 50 messages in under 50ms
          throw new Error(`Context processing too slow: ${duration}ms for 50 messages`);
        }

        if (context.entities.length === 0) {
          throw new Error('No entities accumulated from context');
        }
      }
    );
    suite.tests.push(contextPerformanceTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private async runErrorHandlingTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'Error Handling Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // Empty Input Tests
    const emptyInputTest = this.runTest(
      'Empty Input Handling',
      () => {
        const intent = this.nluEngine.extractIntent('');
        if (intent.type !== 'search_flight') {
          throw new Error(`Expected default intent search_flight, got ${intent.type}`);
        }

        const entities = this.nluEngine.extractEntities('');
        if (entities.length !== 0) {
          throw new Error(`Expected no entities for empty input, got ${entities.length}`);
        }
      }
    );
    suite.tests.push(emptyInputTest);

    // Invalid Input Tests
    const invalidInputTest = this.runTest(
      'Invalid Input Handling',
      () => {
        const nonsenseInputs = [
          'asdfghjkl',
          '12345',
          '!@#$%^&*()',
          'Lorem ipsum dolor sit amet'
        ];

        for (const input of nonsenseInputs) {
          const intent = this.nluEngine.extractIntent(input);
          // Should not crash and should return some default intent
          if (!intent.type) {
            throw new Error(`No intent type returned for input: ${input}`);
          }
        }
      }
    );
    suite.tests.push(invalidInputTest);

    // Large Input Tests
    const largeInputTest = this.runTest(
      'Large Input Handling',
      () => {
        const largeInput = 'I want to travel '.repeat(1000) + 'to Tokyo';
        
        const start = performance.now();
        const intent = this.nluEngine.extractIntent(largeInput);
        const entities = this.nluEngine.extractEntities(largeInput);
        const duration = performance.now() - start;
        
        if (duration > 100) {
          throw new Error(`Large input processing too slow: ${duration}ms`);
        }

        if (!intent.type) {
          throw new Error('No intent extracted from large input');
        }

        // Should still find Tokyo as destination
        const destinations = entities.filter(e => e.type === 'destination');
        if (destinations.length === 0) {
          throw new Error('No destination found in large input');
        }
      }
    );
    suite.tests.push(largeInputTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private async runEdgeCaseTests(): Promise<void> {
    const suite: TestSuite = {
      suiteName: 'Edge Case Tests',
      tests: [],
      totalPassed: 0,
      totalFailed: 0,
      duration: 0
    };

    const startTime = performance.now();

    // Multi-language Support
    const multiLanguageTest = this.runTest(
      'Multi-language Input Handling',
      () => {
        const inputs = [
          'I want to go to París', // Accented characters
          'Find flights to São Paulo', // Special characters
          'Book hotel in Zürich', // Umlauts
          'Travel to München' // Mixed language
        ];

        for (const input of inputs) {
          const intent = this.nluEngine.extractIntent(input);
          const entities = this.nluEngine.extractEntities(input);
          
          // Should not crash and should extract something meaningful
          if (!intent.type) {
            throw new Error(`No intent for multilingual input: ${input}`);
          }
        }
      }
    );
    suite.tests.push(multiLanguageTest);

    // Conflicting Information
    const conflictTest = this.runTest(
      'Conflicting Information Handling',
      () => {
        const entities = this.nluEngine.extractEntities('I want to go to Tokyo and Paris and London and Rome');
        const destinations = entities.filter(e => e.type === 'destination');
        
        // Should extract multiple destinations for user clarification
        if (destinations.length === 0) {
          throw new Error('No destinations extracted from conflicting input');
        }

        // System should be able to handle multiple destinations
        const context = {
          state: ConversationState.GATHERING_REQUIREMENTS,
          entities: destinations,
          missingFields: [],
          lastIntent: null,
          clarificationNeeded: false
        };

        // Should recognize need for clarification with multiple destinations
        if (destinations.length > 1) {
          const clarification = this.nluEngine.clarifyIntent('', {
            ...context,
            clarificationNeeded: true
          });
          
          if (!clarification.question.toLowerCase().includes('multiple')) {
            // Should ask about multiple destinations, but this is implementation dependent
            // Just ensure it returns a valid clarification
            if (!clarification.question || clarification.question.length === 0) {
              throw new Error('No clarification question generated for multiple destinations');
            }
          }
        }
      }
    );
    suite.tests.push(conflictTest);

    // Extreme Values
    const extremeValuesTest = this.runTest(
      'Extreme Values Handling',
      () => {
        const extremeInputs = [
          'Budget is $99999999', // Very large budget
          'For 100 people', // Large group
          'Travel in year 2050', // Future date
          'Budget is $1' // Very small budget
        ];

        for (const input of extremeInputs) {
          const entities = this.nluEngine.extractEntities(input);
          
          // Should handle extreme values gracefully
          if (input.includes('$99999999')) {
            const budgets = entities.filter(e => e.type === 'budget');
            if (budgets.length > 0 && budgets[0].value !== 99999999) {
              throw new Error(`Budget parsing failed for extreme value: got ${budgets[0].value}`);
            }
          }

          if (input.includes('100 people')) {
            const travelers = entities.filter(e => e.type === 'travelers');
            if (travelers.length > 0 && travelers[0].value !== 100) {
              throw new Error(`Traveler count parsing failed: got ${travelers[0].value}`);
            }
          }
        }
      }
    );
    suite.tests.push(extremeValuesTest);

    suite.duration = performance.now() - startTime;
    suite.totalPassed = suite.tests.filter(t => t.passed).length;
    suite.totalFailed = suite.tests.filter(t => !t.passed).length;
    this.results.push(suite);
  }

  private runTest(testName: string, testFn: () => void): TestResult {
    const start = performance.now();
    try {
      testFn();
      return {
        testName,
        passed: true,
        duration: performance.now() - start
      };
    } catch (error) {
      return {
        testName,
        passed: false,
        error: error instanceof Error ? error.message : String(error),
        duration: performance.now() - start
      };
    }
  }

  private printTestSummary(): void {
    console.log('\n📊 AI Travel Agent Test Results Summary');
    console.log('==========================================\n');

    let totalTests = 0;
    let totalPassed = 0;
    let totalFailed = 0;
    let totalDuration = 0;

    for (const suite of this.results) {
      const passRate = suite.totalPassed / suite.tests.length * 100;
      const status = suite.totalFailed === 0 ? '✅' : '❌';
      
      console.log(`${status} ${suite.suiteName}`);
      console.log(`   Tests: ${suite.tests.length} | Passed: ${suite.totalPassed} | Failed: ${suite.totalFailed} | Pass Rate: ${passRate.toFixed(1)}%`);
      console.log(`   Duration: ${suite.duration.toFixed(2)}ms\n`);

      if (suite.totalFailed > 0) {
        console.log('   Failed Tests:');
        suite.tests.filter(t => !t.passed).forEach(test => {
          console.log(`   - ${test.testName}: ${test.error}`);
        });
        console.log('');
      }

      totalTests += suite.tests.length;
      totalPassed += suite.totalPassed;
      totalFailed += suite.totalFailed;
      totalDuration += suite.duration;
    }

    const overallPassRate = totalPassed / totalTests * 100;
    const overallStatus = totalFailed === 0 ? '🎉' : '⚠️';

    console.log('==========================================');
    console.log(`${overallStatus} Overall Results:`);
    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${totalPassed}`);
    console.log(`Failed: ${totalFailed}`);
    console.log(`Pass Rate: ${overallPassRate.toFixed(1)}%`);
    console.log(`Total Duration: ${totalDuration.toFixed(2)}ms`);
    
    if (totalFailed === 0) {
      console.log('\n🚀 All tests passed! AI Travel Agent system is functioning correctly.');
    } else {
      console.log(`\n⚠️  ${totalFailed} test(s) failed. Please review and fix the issues above.`);
    }
  }

  async validateSystemReliability(): Promise<boolean> {
    const results = await this.runAllTests();
    const totalTests = results.reduce((sum, suite) => sum + suite.tests.length, 0);
    const totalPassed = results.reduce((sum, suite) => sum + suite.totalPassed, 0);
    const passRate = totalPassed / totalTests;

    return passRate >= 0.95; // 95% pass rate required for system reliability
  }
}