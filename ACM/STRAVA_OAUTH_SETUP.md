# Strava OAuth Integration Setup

This guide explains how to set up Strava OAuth integration for the InShape application.

## Prerequisites

1. **Strava API Application**: You need to create a Strava API application at [https://www.strava.com/settings/api](https://www.strava.com/settings/api)

## Strava API Setup

1. Go to [Strava Developers](https://www.strava.com/settings/api)
2. Click "Create App" or edit your existing app
3. Fill in the application details:
   - **Application Name**: InShape (or your preferred name)
   - **Category**: Health and Fitness
   - **Club**: Leave empty (optional)
   - **Website**: http://localhost:3000 (or your domain)
   - **Application Description**: Shape-based running challenge tracking
   - **Authorization Callback Domain**: localhost (for development) or your domain
4. After creating the app, note down:
   - **Client ID**
   - **Client Secret**

## Environment Variables Setup

### Backend (.env file in /ACM directory)

Create a `.env` file in the `/ACM` directory with the following variables:

```bash
# Strava OAuth Configuration
STRAVA_CLIENT_ID=your_strava_client_id_here
STRAVA_CLIENT_SECRET=your_strava_client_secret_here
STRAVA_REDIRECT_URI=http://localhost:5000/auth/strava/callback

# Backend Configuration
SECRET_KEY=your_random_secret_key_here
JWT_SECRET=your_jwt_secret_here
FRONTEND_URL=http://localhost:3000

# Production URLs (when deployed)
# STRAVA_REDIRECT_URI=https://yourdomain.com/api/auth/strava/callback
# FRONTEND_URL=https://yourdomain.com
```

### Frontend (.env.local file in /ACM/in-shape-frontend directory)

Create a `.env.local` file in the `/ACM/in-shape-frontend` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
# For production: NEXT_PUBLIC_API_URL=https://yourapi.domain.com
```

## Installation and Setup

1. **Install backend dependencies**:
```bash
cd /ACM
pip install -r requirements.txt
```

2. **Install frontend dependencies**:
```bash
cd /ACM/in-shape-frontend
npm install
```

3. **Generate secure keys for your .env**:
   - `SECRET_KEY`: Use `python -c "import secrets; print(secrets.token_hex(32))"`
   - `JWT_SECRET`: Use `python -c "import secrets; print(secrets.token_hex(32))"`

## Running the Application

1. **Start the backend server**:
```bash
cd /ACM
python backend/app.py
```
Backend will run on `http://localhost:5000`

2. **Start the frontend development server**:
```bash
cd /ACM/in-shape-frontend
npm run dev
```
Frontend will run on `http://localhost:3000`

## OAuth Flow

1. **First-time user experience**:
   - User visits the app at `http://localhost:3000`
   - If not authenticated, they're redirected to `/auth`
   - User clicks "Connect with Strava"
   - User is redirected to Strava for authorization
   - After authorization, user is redirected back to the app
   - User session is created and they can access the full app

2. **Returning users**:
   - Authentication token is stored in localStorage
   - Users are automatically authenticated on subsequent visits
   - Token expires after 24 hours and requires re-authentication

## API Endpoints

The backend provides these OAuth-related endpoints:

- `GET /auth/strava` - Initiate Strava OAuth flow
- `GET /auth/strava/callback` - Handle OAuth callback
- `GET /auth/verify` - Verify user session
- `GET /api/activities` - Get user's Strava activities
- `GET /api/activity/<id>/streams` - Get GPS data for specific activity
- `POST /auth/logout` - Logout user

## Security Features

- **CSRF Protection**: State parameter validation
- **JWT Tokens**: Secure session management
- **Token Expiration**: 24-hour token lifetime
- **Secure Storage**: Tokens stored in localStorage (client-side)

## Troubleshooting

1. **"Strava client ID not configured"**: Make sure your `.env` file has the correct `STRAVA_CLIENT_ID`

2. **CORS errors**: Ensure frontend URL is correctly configured in `FRONTEND_URL` environment variable

3. **OAuth callback fails**: Check that your Strava app's callback domain matches your redirect URI

4. **Token verification fails**: Tokens expire after 24 hours; users need to re-authenticate

## Production Deployment

For production deployment:

1. Update environment variables with production URLs
2. Use a proper database instead of in-memory storage
3. Use Redis or similar for session management
4. Set up proper SSL certificates
5. Configure your production domain in Strava app settings

## File Structure

```
/ACM/
├── backend/
│   ├── app.py                 # Main backend server with OAuth
│   └── procrustes_shape_grader.py
├── in-shape-frontend/
│   ├── src/
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── components/
│   │   │   ├── Navigation.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── app/
│   │       ├── auth/
│   │       │   ├── page.tsx
│   │       │   ├── success/page.tsx
│   │       │   └── error/page.tsx
│   │       └── page.tsx
│   └── .env.local             # Frontend environment variables
├── .env                       # Backend environment variables
└── requirements.txt
```
