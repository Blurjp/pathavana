# Pathavana Authentication System Guide

## Overview

The Pathavana authentication system provides comprehensive security features including:

- JWT-based authentication with access and refresh tokens
- OAuth 2.0 integration (Google, Facebook, Microsoft)
- Email verification and password reset
- Session management with device tracking
- Rate limiting and security middleware
- Audit logging for all authentication events
- Token blacklisting for secure logout
- Multi-factor authentication preparation

## Architecture

### Database Models

1. **User** - Core user account information
2. **UserSession** - Active user sessions with device tracking
3. **TokenBlacklist** - Revoked tokens for security
4. **AuthenticationLog** - Audit trail of all auth events
5. **OAuthConnection** - OAuth provider connections
6. **PasswordResetToken** - Secure password reset tokens

### Security Features

- **Password Requirements**: Minimum 8 characters, uppercase, lowercase, numbers, and special characters
- **Account Lockout**: After 5 failed attempts, account is locked for 30 minutes
- **Token Rotation**: Refresh tokens are rotated on each use
- **Session Management**: Track all active sessions with device information
- **Rate Limiting**: Protect against brute force attacks

## API Endpoints

### Authentication

#### Register New User
```
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "terms_accepted": true,
  "marketing_consent": true
}
```

#### Login
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecureP@ss123
```

#### Refresh Token
```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout
```
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

#### Logout All Sessions
```
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

### OAuth Authentication

#### Get OAuth URL
```
GET /api/v1/auth/oauth-url/{provider}?redirect_uri=http://localhost:3000/auth/callback
```

Providers: `google`, `facebook`, `microsoft`

#### OAuth Login
```
POST /api/v1/auth/{provider}
Content-Type: application/json

{
  "provider": "google",
  "code": "authorization-code-from-provider",
  "state": "random-state-string",
  "redirect_uri": "http://localhost:3000/auth/callback"
}
```

### User Management

#### Get Current User
```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

#### Update Profile
```
PUT /api/v1/auth/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Jane Doe",
  "phone": "+1987654321"
}
```

#### Change Password
```
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldP@ssword123",
  "new_password": "NewSecureP@ss123",
  "logout_other_sessions": true
}
```

### Password Reset

#### Request Password Reset
```
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Reset Password
```
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "password": "NewSecureP@ss123"
}
```

### Email Verification

#### Verify Email
```
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

### Session Management

#### List All Sessions
```
GET /api/v1/auth/sessions
Authorization: Bearer <access_token>
```

#### Revoke Session
```
DELETE /api/v1/auth/sessions/{session_id}
Authorization: Bearer <access_token>
```

## Frontend Integration

### Token Storage

Store tokens securely using httpOnly cookies or secure storage:

```javascript
// Example using httpOnly cookies (recommended)
const login = async (email, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${email}&password=${password}`,
    credentials: 'include', // Include cookies
  });
  
  const data = await response.json();
  // Store tokens in memory for immediate use
  setAccessToken(data.access_token);
  setRefreshToken(data.refresh_token);
};
```

### Automatic Token Refresh

```javascript
const apiClient = axios.create({
  baseURL: '/api/v1',
});

// Request interceptor to add token
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = getRefreshToken();
        const response = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        const data = await response.json();
        setAccessToken(data.access_token);
        setRefreshToken(data.refresh_token);
        
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

### OAuth Flow

```javascript
// 1. Get OAuth URL
const loginWithGoogle = async () => {
  const response = await fetch('/api/v1/auth/oauth-url/google?' + 
    new URLSearchParams({
      redirect_uri: window.location.origin + '/auth/callback',
    })
  );
  
  const data = await response.json();
  // Save state for CSRF protection
  localStorage.setItem('oauth_state', data.state);
  // Redirect to OAuth provider
  window.location.href = data.auth_url;
};

// 2. Handle OAuth callback
const handleOAuthCallback = async () => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  
  // Verify state
  const savedState = localStorage.getItem('oauth_state');
  if (state !== savedState) {
    throw new Error('Invalid state parameter');
  }
  
  // Exchange code for tokens
  const response = await fetch('/api/v1/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider: 'google',
      code,
      state,
      redirect_uri: window.location.origin + '/auth/callback',
    }),
  });
  
  const data = await response.json();
  // Store tokens and redirect
  setAccessToken(data.access_token);
  setRefreshToken(data.refresh_token);
  window.location.href = '/dashboard';
};
```

## Security Best Practices

### 1. Token Storage
- Use httpOnly cookies for refresh tokens
- Store access tokens in memory or secure storage
- Never store tokens in localStorage for sensitive applications

### 2. HTTPS Only
- Always use HTTPS in production
- Set secure flag on cookies
- Use HSTS headers

### 3. CORS Configuration
- Whitelist specific origins
- Don't use wildcard (*) in production
- Configure appropriate headers

### 4. Rate Limiting
The API implements rate limiting on sensitive endpoints:
- Login: 5 attempts per 5 minutes
- Register: 3 attempts per hour
- Password reset: 3 attempts per hour

### 5. Session Security
- Implement session timeouts
- Allow users to view and revoke sessions
- Track device information for anomaly detection

### 6. Password Security
- Enforce strong password requirements
- Use bcrypt for password hashing
- Implement account lockout after failed attempts

## Environment Configuration

Create a `.env` file with the following variables:

```env
# Security
SECRET_KEY="use-openssl-rand-hex-32-to-generate"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Providers
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
FACEBOOK_APP_ID="your-facebook-app-id"
FACEBOOK_APP_SECRET="your-facebook-app-secret"
MICROSOFT_CLIENT_ID="your-microsoft-client-id"
MICROSOFT_CLIENT_SECRET="your-microsoft-client-secret"

# Email Configuration
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
SMTP_FROM_EMAIL="noreply@pathavana.com"
SMTP_FROM_NAME="Pathavana"

# Frontend URL
FRONTEND_URL="http://localhost:3000"
```

## Database Migration

Run the following to create authentication tables:

```bash
# Create migration
alembic revision --autogenerate -m "Add authentication tables"

# Apply migration
alembic upgrade head
```

## Testing

Test the authentication system:

```bash
# Run tests
pytest tests/test_auth.py

# Test specific endpoint
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestP@ss123",
    "full_name": "Test User",
    "terms_accepted": true
  }'
```

## Monitoring and Logging

The system logs all authentication events:

1. **Login attempts** (successful and failed)
2. **Registration** events
3. **Password resets**
4. **Email verifications**
5. **OAuth logins**
6. **Session creation/deletion**
7. **Token refresh**
8. **Account lockouts**

Access logs through the `authentication_logs` table or your logging system.

## Troubleshooting

### Common Issues

1. **"Invalid credentials"**
   - Check email/password
   - Verify account is not locked
   - Check if email is verified

2. **"Token expired"**
   - Implement automatic token refresh
   - Check token expiration settings

3. **"Rate limit exceeded"**
   - Wait for the specified period
   - Check rate limit configuration

4. **OAuth errors**
   - Verify OAuth credentials
   - Check redirect URI matches configuration
   - Ensure proper CORS settings

## Future Enhancements

The authentication system is prepared for:

1. **Multi-Factor Authentication (MFA)**
   - TOTP support
   - SMS verification
   - Email codes

2. **Advanced Security**
   - Device fingerprinting
   - Geolocation tracking
   - Anomaly detection

3. **Enterprise Features**
   - SAML support
   - Active Directory integration
   - Role-based access control (RBAC)

4. **Compliance**
   - GDPR data export
   - Account deletion
   - Consent management