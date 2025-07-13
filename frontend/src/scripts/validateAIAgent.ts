#!/usr/bin/env node

/**
 * AI Travel Agent Validation Script
 * Run this script to validate all AI Travel Agent functionality
 */

import { AIAgentTestRunner } from '../tests/AIAgentTestRunner';

async function validateAITravelAgent() {
  console.log('🤖 AI Travel Agent System Validation');
  console.log('====================================\n');

  const testRunner = new AIAgentTestRunner();
  
  try {
    const isReliable = await testRunner.validateSystemReliability();
    
    if (isReliable) {
      console.log('\n✅ System Validation: PASSED');
      console.log('The AI Travel Agent system is ready for production use.');
      process.exit(0);
    } else {
      console.log('\n❌ System Validation: FAILED');
      console.log('The AI Travel Agent system needs fixes before production use.');
      process.exit(1);
    }
  } catch (error) {
    console.error('\n💥 Validation Error:', error);
    process.exit(1);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  validateAITravelAgent();
}

export { validateAITravelAgent };