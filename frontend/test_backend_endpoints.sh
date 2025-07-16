#!/bin/bash

# Backend endpoint testing script
BASE_URL="http://localhost:8001"
API_V1="${BASE_URL}/api/v1"

echo "=== Testing Backend Endpoints ==="
echo ""

# 1. Health check
echo "1. Health Check:"
curl -s "${BASE_URL}/health" | jq . || echo "FAILED"
echo ""

# 2. Create new session
echo "2. Create New Session (POST /api/v1/travel/sessions/new):"
SESSION_RESPONSE=$(curl -s -X POST "${API_V1}/travel/sessions/new" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json")
echo "$SESSION_RESPONSE" | jq .
SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.data.session_id // empty')
echo "Session ID: $SESSION_ID"
echo ""

# 3. Get session
if [ -n "$SESSION_ID" ]; then
  echo "3. Get Session (GET /api/v1/travel/sessions/{id}):"
  curl -s "${API_V1}/travel/sessions/${SESSION_ID}" \
    -H "Accept: application/json" | jq .
  echo ""
fi

# 4. List sessions
echo "4. List Sessions (GET /api/v1/travel/sessions):"
curl -s "${API_V1}/travel/sessions" \
  -H "Accept: application/json" | jq .
echo ""

# 5. Auth endpoints
echo "5. Auth Me (GET /api/v1/auth/me) - Should fail without auth:"
curl -s "${API_V1}/auth/me" \
  -H "Accept: application/json" | jq .
echo ""

# 6. Travelers endpoint - requires auth
echo "6. List Travelers (GET /api/v1/travelers) - Should fail without auth:"
curl -s "${API_V1}/travelers" \
  -H "Accept: application/json" | jq .
echo ""

# 7. Check OpenAPI docs
echo "7. OpenAPI Documentation:"
echo "Docs URL: ${API_V1}/docs"
echo "OpenAPI URL: ${API_V1}/openapi.json"
curl -s -o /dev/null -w "Docs Status: %{http_code}\n" "${API_V1}/docs"
curl -s -o /dev/null -w "OpenAPI Status: %{http_code}\n" "${API_V1}/openapi.json"
echo ""

# 8. Root endpoint
echo "8. Root Endpoint (GET /):"
curl -s "${BASE_URL}/" | jq .
echo ""

echo "=== Testing Complete ==="