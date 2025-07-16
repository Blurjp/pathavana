# AI Agent Configuration Guide

This guide explains how to configure the AI agent in Pathavana to enable intelligent travel planning responses.

## Overview

Pathavana uses an AI-powered orchestrator to provide intelligent travel planning assistance. Without proper configuration, the system falls back to basic template responses.

## Quick Start

### Option 1: Using OpenAI (Recommended for Quick Setup)

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Edit `backend/.env`:
   ```env
   LLM_PROVIDER="openai"
   OPENAI_API_KEY="your-openai-api-key-here"
   LLM_MODEL="gpt-4"  # or "gpt-3.5-turbo" for lower cost
   ```
3. Restart the backend server

### Option 2: Using Azure OpenAI

1. Set up Azure OpenAI service in Azure Portal
2. Create a deployment for your chosen model
3. Edit `backend/.env`:
   ```env
   LLM_PROVIDER="azure_openai"
   AZURE_OPENAI_API_KEY="your-azure-key"
   AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   AZURE_OPENAI_API_VERSION="2024-02-01"
   ```
4. Restart the backend server

### Option 3: Using Anthropic Claude

1. Get an API key from https://console.anthropic.com/
2. Edit `backend/.env`:
   ```env
   LLM_PROVIDER="anthropic"
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   LLM_MODEL="claude-3-opus-20240229"  # or other Claude models
   ```
3. Restart the backend server

## Configuration Details

### LLM Settings

These settings apply regardless of provider:

```env
# Model temperature (0.0-1.0, higher = more creative)
LLM_TEMPERATURE=0.7

# Maximum tokens in response
LLM_MAX_TOKENS=2000

# Enable streaming responses
LLM_STREAMING_ENABLED=true

# Cache responses for this many seconds
LLM_CACHE_TTL=3600
```

### Testing Your Configuration

1. Run the AI agent test script:
   ```bash
   cd backend
   python test_ai_agent_fix.py
   ```

2. Check the backend logs:
   ```bash
   tail -f backend/logs/app.log
   ```

3. Look for these success indicators:
   - "✅ UnifiedOrchestrator initialized successfully"
   - AI responses that are contextual and varied
   - No template responses like "I understand. Where would you like to travel?"

## Troubleshooting

### Common Issues

1. **"AI Orchestrator not available - using template responses"**
   - Check your LLM provider credentials
   - Ensure the API key is valid and has sufficient credits
   - Verify the endpoint URL (for Azure)

2. **"ModuleNotFoundError" or Import Errors**
   - Run `pip install -r requirements.txt` in the backend directory
   - Ensure you're using the virtual environment

3. **Responses are still template-based despite configuration**
   - Double-check the .env file formatting (no spaces around '=')
   - Ensure environment variables are loaded (restart server)
   - Check for typos in variable names

### Verifying AI Responses

**Template Response (No AI):**
```
I understand. Where would you like to travel? When are you planning to travel? How many people will be traveling?
```

**AI Response (Working Properly):**
```
I'd be happy to help you plan your trip to Paris! Paris is beautiful next month with mild weather perfect for sightseeing. To help create the ideal itinerary, could you tell me:
- Your specific travel dates in next month?
- How many days you're planning to stay?
- What interests you most - museums, food, shopping, or historic sites?
```

## Cost Considerations

- **OpenAI GPT-3.5-turbo**: ~$0.001 per request (most economical)
- **OpenAI GPT-4**: ~$0.03 per request (best quality)
- **Azure OpenAI**: Similar to OpenAI pricing
- **Anthropic Claude**: Competitive pricing, check current rates

## Security Notes

1. Never commit API keys to version control
2. Use environment variables or secure key vaults
3. Rotate API keys regularly
4. Monitor usage to prevent unexpected charges

## Advanced Configuration

### Using Multiple Providers

You can configure fallback providers by implementing logic in `llm_service.py`:

```python
# Primary provider
primary_llm = get_llm("openai")

# Fallback provider
if not primary_llm:
    fallback_llm = get_llm("anthropic")
```

### Custom Model Parameters

Adjust model behavior for specific use cases:

```env
# For factual responses
LLM_TEMPERATURE=0.3

# For creative suggestions
LLM_TEMPERATURE=0.8

# For detailed planning
LLM_MAX_TOKENS=4000
```

## Monitoring

1. Check response quality regularly
2. Monitor API usage and costs
3. Review user feedback on AI responses
4. Adjust temperature and prompts as needed

## Getting Help

If you continue to experience issues:

1. Check the backend logs for detailed error messages
2. Run the test script with verbose output
3. Verify API quotas and limits with your provider
4. Consider reaching out to the provider's support

Remember: The AI agent significantly enhances the user experience by providing contextual, helpful travel planning assistance instead of rigid template responses.