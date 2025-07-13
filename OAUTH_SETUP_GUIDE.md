# OAuth Setup Guide for Pathavana

This guide will help you set up OAuth authentication for Google and Facebook in the Pathavana application.

## Prerequisites

- A Google Cloud Console account
- A Facebook Developer account
- The application running on http://localhost:3000 (frontend) and http://localhost:8001 (backend)

## Google OAuth Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "Pathavana")
4. Click "Create"

### 2. Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in the required fields:
     - App name: Pathavana
     - User support email: your email
     - Developer contact: your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if in development
4. Back in credentials, create OAuth client ID:
   - Application type: "Web application"
   - Name: "Pathavana Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://localhost:8001`
   - Authorized redirect URIs:
     - `http://localhost:3000/auth/callback`
5. Click "Create"
6. Copy the Client ID and Client Secret

### 4. Configure Environment Variables

Add to your backend `.env` file:
```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## Facebook OAuth Setup

### 1. Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Consumer" as the app type
4. Fill in the app details:
   - App name: Pathavana
   - App contact email: your email
5. Click "Create App"

### 2. Set Up Facebook Login

1. In your app dashboard, click "Add Product"
2. Find "Facebook Login" and click "Set Up"
3. Choose "Web"
4. Site URL: `http://localhost:3000`
5. Go to Facebook Login → Settings
6. Add to Valid OAuth Redirect URIs:
   - `http://localhost:3000/auth/callback`
7. Save Changes

### 3. Get App Credentials

1. Go to Settings → Basic
2. Copy the App ID and App Secret
3. Add to your backend `.env` file:
```env
FACEBOOK_APP_ID=your_facebook_app_id_here
FACEBOOK_APP_SECRET=your_facebook_app_secret_here
```

## Frontend Configuration

Create a `.env.local` file in the frontend directory:
```env
REACT_APP_API_BASE_URL=http://localhost:8001
REACT_APP_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

## Testing OAuth

1. Start the backend server:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

2. Start the frontend:
```bash
cd frontend
npm start
```

3. Try logging in with Google or Facebook through the login modal

## Production Considerations

When deploying to production:

1. Update all URLs to use your production domain
2. Use HTTPS for all URLs
3. Update OAuth redirect URIs in Google and Facebook consoles
4. Ensure environment variables are securely stored
5. Consider implementing:
   - Rate limiting for OAuth endpoints
   - Session management
   - Token refresh logic
   - Proper error handling and logging

## Troubleshooting

### Common Issues

1. **"Redirect URI mismatch"**: Ensure the redirect URI in your app exactly matches what's configured in the OAuth provider
2. **"Invalid client"**: Check that your client ID and secret are correctly set in environment variables
3. **CORS errors**: Make sure your backend CORS settings include your frontend URL
4. **"This app is in development mode"**: Add test users in Google/Facebook console for testing

### Debug Tips

- Check browser console for JavaScript errors
- Check network tab for failed API calls
- Verify backend logs for OAuth errors
- Ensure all environment variables are loaded correctly

## Security Notes

- Never commit OAuth credentials to version control
- Use environment variables for all sensitive data
- Implement CSRF protection (already done with state parameter)
- Validate all OAuth responses on the backend
- Use HTTPS in production for all OAuth flows