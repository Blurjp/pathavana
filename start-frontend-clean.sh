#!/bin/bash

echo "Starting Pathavana Frontend with OAuth-safe configuration..."

# Navigate to frontend directory
cd frontend

# Clear browser cache for localhost:3000
echo "Please clear your browser cache for localhost:3000 before testing OAuth"

# Kill any existing processes
pkill -f "node.*react-scripts" || true
pkill -f "node.*craco" || true

# Clear node modules cache
echo "Clearing node modules cache..."
rm -rf node_modules/.cache

# Set environment variables
export FAST_REFRESH=false
export DISABLE_ESLINT_PLUGIN=true

# Start the frontend
echo "Starting frontend with hot reload disabled..."
npm start