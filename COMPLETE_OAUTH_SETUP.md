# Complete OAuth Setup

## Current Status ✅

- ✅ Google Client ID is configured
- ❌ Google Client Secret is missing  
- ❌ Facebook App ID and Secret are missing

## Quick Fix (2 minutes)

### Step 1: Get Google Client Secret

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one that has Client ID: `55013767303-slk94mloce0s2l4ipqdftbtobflppksf`)
3. Go to "APIs & Services" → "Credentials"
4. Find your OAuth 2.0 Client ID
5. Click on it and copy the "Client Secret"

### Step 2: Add Google Client Secret

Edit `backend/.env` and update line 32:
```env
GOOGLE_CLIENT_SECRET="your_actual_google_client_secret_here"
```

### Step 3: (Optional) Set up Facebook OAuth

If you want Facebook login:

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or use existing
3. Add Facebook Login product
4. Configure OAuth redirect URI: `http://localhost:3000/auth/callback`
5. Get App ID and App Secret

Edit `backend/.env` lines 35-36:
```env
FACEBOOK_APP_ID="your_facebook_app_id"
FACEBOOK_APP_SECRET="your_facebook_app_secret"
```

### Step 4: Restart Backend

The backend server will automatically pick up the new credentials.

### Step 5: Test

1. Check config: http://localhost:8001/api/v1/frontend-config
2. Try Google login button

## Verification

After adding the Google Client Secret, you should see:
```json
{
  "features": {
    "googleOAuth": true,
    "facebookOAuth": false  // or true if you added Facebook
  }
}
```

## Current OAuth Setup

Your Google OAuth app should be configured with:
- **Authorized JavaScript origins**: `http://localhost:3000`, `http://localhost:8001`
- **Authorized redirect URIs**: `http://localhost:3000/auth/callback`

If these aren't set up, add them in Google Cloud Console → APIs & Services → Credentials → Your OAuth Client.