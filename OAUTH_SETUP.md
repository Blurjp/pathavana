# OAuth Setup

The frontend now automatically reads configuration from the backend's `.env` file.

## Current Status

When you click Google/Facebook login, you'll see:
- **"Google OAuth not configured"** or **"Facebook OAuth not configured"**

## Setup OAuth (5 minutes)

### 1. Create Backend Environment File

Copy the demo file:
```bash
cd backend
cp .env.demo .env
```

### 2. Get OAuth Credentials

#### Google OAuth:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Google+ API → Create OAuth 2.0 credentials
3. Add redirect URI: `http://localhost:3000/auth/callback`
4. Copy Client ID and Secret

#### Facebook OAuth:
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create app → Add Facebook Login
3. Add redirect URI: `http://localhost:3000/auth/callback`
4. Copy App ID and Secret

### 3. Add Credentials to Backend

Edit `backend/.env`:
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

### 4. Restart Backend

The backend will automatically detect the new credentials.

## Check Configuration

Visit: http://localhost:8001/api/v1/frontend-config

You should see:
```json
{
  "features": {
    "googleOAuth": true,
    "facebookOAuth": true
  }
}
```

## Test OAuth

Click Google/Facebook login buttons - they should now redirect to OAuth providers!

For detailed setup instructions, see [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md)