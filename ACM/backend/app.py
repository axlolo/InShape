#!/usr/bin/env python3
"""
In Shape Backend Server
Handles Strava OAuth authentication and activity data retrieval
"""

import os
import json
import jwt
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import secrets
import logging
from database import db_service
import math

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
CORS(app, origins=['http://localhost:3000'])

# Strava OAuth configuration
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:5000/auth/strava/callback')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
JWT_EXPIRATION_HOURS = 24

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_polyline(polyline_str):
    """Decode a polyline to a list of [lat, lng] pairs. Supports Google Encoded Polyline Algorithm Format."""
    if not polyline_str:
        return []
    index, lat, lng = 0, 0, 0
    coordinates = []
    length = len(polyline_str)

    while index < length:
        result, shift = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        result, shift = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append([lat / 1e5, lng / 1e5])

    return coordinates

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'in-shape-backend'}), 200

@app.route('/auth/strava', methods=['GET'])
def strava_auth():
    """Initiate Strava OAuth flow"""
    if not STRAVA_CLIENT_ID:
        return jsonify({'error': 'Strava client ID not configured'}), 500
    
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in session (in production, use proper session storage)
    # For now, we'll return it and expect the frontend to pass it back
    
    auth_params = {
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': STRAVA_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read,activity:read_all',
        'state': state
    }
    
    auth_url = 'https://www.strava.com/oauth/authorize?' + urlencode(auth_params)
    
    return jsonify({
        'auth_url': auth_url,
        'state': state
    })

@app.route('/auth/strava/callback', methods=['GET'])
def strava_callback():
    """Handle Strava OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'{FRONTEND_URL}/auth/error?error={error}')
    
    if not code:
        return redirect(f'{FRONTEND_URL}/auth/error?error=no_code')
    
    # Exchange code for access token
    try:
        token_data = exchange_code_for_token(code)
        if 'access_token' not in token_data:
            return redirect(f'{FRONTEND_URL}/auth/error?error=token_exchange_failed')
        
        # Get athlete data
        athlete_data = get_athlete_data(token_data['access_token'])
        
        # Create user session (no database storage)
        user_id = str(athlete_data['id'])
        session_token = create_user_session_simple(user_id, token_data, athlete_data)
        
        # Redirect to frontend with session token
        return redirect(f'{FRONTEND_URL}/auth/success?token={session_token}')
        
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        return redirect(f'{FRONTEND_URL}/auth/error?error=server_error')

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    token_url = 'https://www.strava.com/oauth/token'
    
    data = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    return response.json()

def get_athlete_data(access_token):
    """Get authenticated athlete data from Strava"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
    response.raise_for_status()
    
    return response.json()

def refresh_strava_token(refresh_token):
    """Refresh expired Strava access token using refresh token"""
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        logger.error("Strava client credentials not configured")
        raise ValueError("Strava client credentials not configured")
    
    token_url = 'https://www.strava.com/oauth/token'
    
    data = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    logger.info(f"Attempting token refresh for client_id: {STRAVA_CLIENT_ID}")
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
        response.raise_for_status()
    
    result = response.json()
    logger.info(f"Token refresh successful")
    return result

def get_valid_access_token(user_id):
    """Get a valid access token for user, refreshing if necessary"""
    logger.info(f"Getting valid access token for user {user_id}")
    
    # First try to get an active (non-expired) token
    token_record = db_service.get_active_token(user_id)
    if token_record:
        logger.info(f"Found active token for user {user_id}")
        return token_record.access_token
    
    # If no active token, try to refresh the latest token
    logger.info(f"No active token found, looking for latest token to refresh for user {user_id}")
    latest_token = db_service.get_latest_token(user_id)
    if not latest_token:
        logger.error(f"No token found in database for user {user_id}")
        return None
    
    logger.info(f"Found latest token for user {user_id}, expires at: {latest_token.expires_at}")
    
    try:
        # Refresh the token
        logger.info(f"Refreshing expired token for user {user_id}")
        new_token_data = refresh_strava_token(latest_token.refresh_token)
        
        # Store the new token
        db_service.store_user_tokens(user_id, new_token_data)
        logger.info(f"Successfully refreshed and stored new token for user {user_id}")
        
        return new_token_data['access_token']
        
    except Exception as e:
        logger.error(f"Failed to refresh token for user {user_id}: {e}")
        return None

def make_strava_request(url, access_token, user_id, params=None):
    """Make a Strava API request with automatic token refresh on 401"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 401:
            # Token expired, try to refresh
            logger.info(f"Token expired for user {user_id}, attempting refresh")
            new_access_token = get_valid_access_token(user_id)
            if new_access_token:
                headers = {'Authorization': f'Bearer {new_access_token}'}
                response = requests.get(url, headers=headers, params=params)
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"Strava API request failed for user {user_id}: {e}")
        raise

def create_user_session_simple(user_id, token_data, athlete_data):
    """Create a user session and return JWT token (no database storage)"""
    # Create JWT token with user data and Strava tokens
    payload = {
        'user_id': user_id,
        'access_token': token_data['access_token'],
        'refresh_token': token_data['refresh_token'],
        'athlete_data': athlete_data,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def create_user_session(user_id, token_data, athlete_data):
    """Create a user session and return JWT token (legacy - with database storage)"""
    # Create JWT token
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    
    # Store session in database
    expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    db_service.create_user_session(
        user_id=user_id,
        jwt_token=token,
        expires_at=expires_at,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return token

@app.route('/auth/verify', methods=['GET'])
def verify_token():
    """Verify user session token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Check if this is the new token format with athlete data
        if 'athlete_data' in payload:
            # New format - athlete data is in the JWT
            athlete_data = payload['athlete_data']
        else:
            # Legacy format - try to get user from database
            user = db_service.get_user(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Convert user to athlete data format for frontend compatibility
            athlete_data = {
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'profile': user.profile_url,
                'profile_medium': user.profile_medium_url,
                'city': user.city,
                'state': user.state,
                'country': user.country,
                'sex': user.sex,
                'created_at': user.strava_created_at.isoformat() if user.strava_created_at else None,
                'premium': user.premium
            }
        
        return jsonify({
            'user_id': user_id,
            'athlete': athlete_data,
            'authenticated': True
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/api/activities/recent', methods=['GET'])
def get_recent_activities():
    """Get user's recent running activities within a timeframe (default last 60 days)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token (with automatic refresh if needed)
        if 'access_token' in payload:
            # For JWT tokens, we need to check if they're expired and handle refresh
            access_token = payload['access_token']
            # Try a test request to see if token is still valid
            try:
                test_headers = {'Authorization': f'Bearer {access_token}'}
                test_response = requests.get('https://www.strava.com/api/v3/athlete', headers=test_headers)
                if test_response.status_code == 401:
                    logger.info(f"JWT access token expired for user {user_id}, attempting refresh")
                    # Try to refresh using refresh_token from JWT
                    if 'refresh_token' in payload:
                        new_token_data = refresh_strava_token(payload['refresh_token'])
                        access_token = new_token_data['access_token']
                        # Store the new token in database for future use
                        db_service.store_user_tokens(user_id, new_token_data)
                        logger.info(f"Successfully refreshed JWT token for user {user_id}")
                    else:
                        # Fallback to database token refresh
                        access_token = get_valid_access_token(user_id)
            except Exception as e:
                logger.warning(f"JWT token test failed for user {user_id}: {e}, trying database fallback")
                access_token = get_valid_access_token(user_id)
        else:
            access_token = get_valid_access_token(user_id)
            
        if not access_token:
            return jsonify({
                'error': 'Strava authentication expired', 
                'auth_required': True,
                'message': 'Please reconnect with Strava to access your activities'
            }), 401
        
        # Timeframe: default last 60 days; allow override via query param
        from datetime import datetime, timezone, timedelta
        try:
            days_param = request.args.get('days', default=None, type=int)
        except Exception:
            days_param = None
        days = days_param if days_param and days_param > 0 else 60
        after_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        
        params = {
            'after': after_timestamp,
            'per_page': 200  # fetch as many as possible in single page
        }
        
        # Use the new helper that handles token refresh on 401
        try:
            activities = make_strava_request(
                'https://www.strava.com/api/v3/athlete/activities',
                access_token,
                user_id,
                params
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Try one more time with a fresh token from database
                fresh_token = get_valid_access_token(user_id)
                if fresh_token:
                    activities = make_strava_request(
                        'https://www.strava.com/api/v3/athlete/activities',
                        fresh_token,
                        user_id,
                        params
                    )
                else:
                    raise
            else:
                raise
        
        # Filter for running activities only; don't require polyline here
        running_activities = []
        for activity in activities:
            try:
                if activity.get('type') != 'Run':
                    continue
                # Annotate whether a polyline is available for UI/debugging
                amap = activity.get('map') or {}
                activity['has_map_polyline'] = bool(amap.get('summary_polyline') or amap.get('polyline'))
                running_activities.append(activity)
            except Exception:
                # Skip any malformed entries safely
                continue
        
        # Optionally include precomputed grades for each run
        include_grades = request.args.get('include_grades', 'false').lower() == 'true'
        shape = (request.args.get('shape') or 'rectangle').lower()
        
        if include_grades:
            graded_activities = []
            for activity in running_activities:
                act = dict(activity)  # shallow copy to annotate
                act_id = act.get('id')
                act_user_id = user_id
                try:
                    # Check cache first (default to procrustes method for pre-grading)
                    existing = db_service.get_challenge_score(act_user_id, str(act_id), shape)
                    if existing:
                        act['challenge_score'] = round(existing.score, 2)
                        act['challenge_grade'] = existing.letter_grade
                        act['challenge_cached'] = True
                        act['graded'] = True
                        graded_activities.append(act)
                        continue
                    
                    # Try to fetch streams
                    streams = None
                    try:
                        streams = fetch_activity_streams(access_token, act_id)
                    except requests.exceptions.HTTPError:
                        streams = None
                    except Exception:
                        streams = None
                    
                    # Fallback to polyline if needed
                    if not streams or 'latlng' not in streams or not streams['latlng'].get('data'):
                        try:
                            headers = {'Authorization': f'Bearer {access_token}'}
                            act_resp = requests.get(
                                f'https://www.strava.com/api/v3/activities/{act_id}',
                                headers=headers,
                                params={'include_all_efforts': 'false'}
                            )
                            act_resp.raise_for_status()
                            act_full = act_resp.json()
                            polyline = None
                            if isinstance(act_full, dict):
                                polyline = (act_full.get('map') or {}).get('summary_polyline') or (act_full.get('map') or {}).get('polyline')
                            if polyline:
                                coords = decode_polyline(polyline)
                                if coords:
                                    streams = streams or {}
                                    streams['latlng'] = {'data': coords}
                        except Exception:
                            pass
                    
                    if not streams or 'latlng' not in streams or not streams['latlng'].get('data'):
                        act['graded'] = False
                        act['challenge_error'] = 'No GPS data'
                        graded_activities.append(act)
                        continue
                    
                    # Create temp file and grade similarity (score only)
                    import tempfile
                    import json as _json
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        _json.dump({'coordinates': streams['latlng']['data'], 'activity_id': act_id}, temp_file)
                        temp_gps_file = temp_file.name
                    
                    try:
                        base_path = '/Users/axeledin/Desktop/ACM_Folder/ACM/in-shape-frontend/public/shapes'
                        shape_file_map = {
                            'rectangle': f'{base_path}/rectangle-1.svg',
                            'circle': f'{base_path}/circle-1.svg',
                            'triangle': f'{base_path}/triangle-1.svg',
                            'heart': f'{base_path}/heart-1.svg',
                            'star': f'{base_path}/star-1.svg'
                        }
                        svg_file = shape_file_map.get(shape)
                        if not svg_file or not os.path.exists(svg_file):
                            act['graded'] = False
                            act['challenge_error'] = f'Shape file not found for {shape}'
                        else:
                            from procrustes_shape_grader import grade_shape_similarity_procrustes
                            score_val = grade_shape_similarity_procrustes(temp_gps_file, svg_file)
                            letter = get_letter_grade(score_val)
                            # Store in DB (use procrustes for pre-grading)
                            db_service.store_challenge_score(act_user_id, str(act_id), shape, score_val, letter)
                            act['challenge_score'] = round(score_val, 2)
                            act['challenge_grade'] = letter
                            act['challenge_cached'] = False
                            act['graded'] = True
                    finally:
                        try:
                            os.unlink(temp_gps_file)
                        except Exception:
                            pass
                except Exception as e:
                    act['graded'] = False
                    act['challenge_error'] = 'Grading failed'
                    logger.warning(f"Failed to pre-grade activity {act_id}: {e}")
                graded_activities.append(act)
            running_activities = graded_activities
        
        return jsonify({
            'activities': running_activities,
            'count': len(running_activities),
            'timeframe': f'{days} days',
            'include_grades': include_grades,
            'shape': shape if include_grades else None
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        return jsonify({'error': 'Failed to fetch recent activities'}), 500

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """Get user's Strava activities"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token from JWT (new format) or database (legacy)
        access_token = None
        if 'access_token' in payload:
            # New format - token is in JWT
            access_token = payload['access_token']
        else:
            # Legacy format - get from database
            token_record = db_service.get_active_token(user_id)
            if not token_record:
                return jsonify({'error': 'No valid Strava token found'}), 401
            access_token = token_record.access_token
        
        if not access_token:
            return jsonify({'error': 'No valid Strava token available'}), 401
        
        # Fetch activities from Strava
        activities = fetch_strava_activities(access_token)
        
        return jsonify({'activities': activities})
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error fetching activities: {e}")
        return jsonify({'error': 'Failed to fetch activities'}), 500

def fetch_all_strava_activities(access_token):
    """Fetch ALL activities from Strava API using pagination"""
    headers = {'Authorization': f'Bearer {access_token}'}
    all_activities = []
    page = 1
    per_page = 200  # Maximum allowed by Strava
    
    logger.info("🔄 Starting to fetch all activities from Strava API...")
    
    while True:
        params = {'per_page': per_page, 'page': page}
        
        logger.info(f"📥 Fetching page {page} (up to {per_page} activities)...")
        
        response = requests.get('https://www.strava.com/api/v3/athlete/activities', 
                              headers=headers, params=params)
        response.raise_for_status()
        
        activities = response.json()
        
        # If we get fewer activities than requested, we've reached the end
        if not activities or len(activities) < per_page:
            all_activities.extend(activities)
            logger.info(f"📋 Page {page}: Retrieved {len(activities)} activities (final page)")
            break
            
        all_activities.extend(activities)
        logger.info(f"📋 Page {page}: Retrieved {len(activities)} activities (total so far: {len(all_activities)})")
        page += 1
        
        # Safety check to prevent infinite loops
        if page > 100:  # Max 20,000 activities
            logger.warning("⚠️  Reached maximum page limit for activity fetching")
            break
    
    logger.info(f"✅ Completed fetching {len(all_activities)} total activities from Strava")
    return all_activities

def fetch_strava_activities(access_token, per_page=30):
    """Fetch activities from Strava API (limited)"""
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': per_page}
    
    response = requests.get('https://www.strava.com/api/v3/athlete/activities', 
                          headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

@app.route('/api/activity/<int:activity_id>/streams', methods=['GET'])
def get_activity_streams(activity_id):
    """Get detailed GPS data for a specific activity"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token from JWT (new format) or database (legacy)
        access_token = None
        if 'access_token' in payload:
            # New format - token is in JWT
            access_token = payload['access_token']
        else:
            # Legacy format - get from database
            token_record = db_service.get_active_token(user_id)
            if not token_record:
                return jsonify({'error': 'No valid Strava token found'}), 401
            access_token = token_record.access_token
        
        if not access_token:
            return jsonify({'error': 'No valid Strava token available'}), 401
        
        # Fetch activity streams from Strava
        streams = fetch_activity_streams(access_token, activity_id)
        
        return jsonify({'streams': streams})
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error fetching activity streams: {e}")
        return jsonify({'error': 'Failed to fetch activity streams'}), 500

def fetch_activity_streams(access_token, activity_id):
    """Fetch activity streams (GPS data) from Strava API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    stream_types = 'latlng,distance,time'
    
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams'
    params = {'keys': stream_types, 'key_by_type': 'true'}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

def fetch_athlete_stats(access_token, athlete_id):
    """Fetch athlete statistics from Strava API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    url = f'https://www.strava.com/api/v3/athletes/{athlete_id}/stats'
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

def calculate_comprehensive_stats(activities):
    """Calculate comprehensive stats from all activities"""
    from datetime import datetime, timezone, timedelta
    
    logger.info(f"🧮 Starting to calculate stats from {len(activities)} activities...")
    
    now = datetime.now(timezone.utc)
    
    # Calculate different time periods
    week_start = now - timedelta(days=now.weekday())  # This week (Monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # This month
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)  # This year
    
    logger.info(f"📅 Calculating stats for periods:")
    logger.info(f"   • This week: {week_start.strftime('%Y-%m-%d')} to now")
    logger.info(f"   • This month: {month_start.strftime('%Y-%m-%d')} to now") 
    logger.info(f"   • This year: {year_start.strftime('%Y-%m-%d')} to now")
    
    # Initialize stats
    stats = {
        'this_week_run_totals': {'count': 0, 'distance': 0.0, 'moving_time': 0, 'elapsed_time': 0, 'elevation_gain': 0.0},
        'this_month_run_totals': {'count': 0, 'distance': 0.0, 'moving_time': 0, 'elapsed_time': 0, 'elevation_gain': 0.0},
        'ytd_run_totals': {'count': 0, 'distance': 0.0, 'moving_time': 0, 'elapsed_time': 0, 'elevation_gain': 0.0},
        'all_run_totals': {'count': 0, 'distance': 0.0, 'moving_time': 0, 'elapsed_time': 0, 'elevation_gain': 0.0},
        'recent_run_totals': {'count': 0, 'distance': 0.0, 'moving_time': 0, 'elapsed_time': 0, 'elevation_gain': 0.0}
    }
    
    recent_cutoff = now - timedelta(days=28)  # Last 4 weeks
    
    processed_count = 0
    run_count = 0
    
    for activity in activities:
        processed_count += 1
        
        # Log progress every 100 activities
        if processed_count % 100 == 0:
            logger.info(f"📊 Processed {processed_count}/{len(activities)} activities ({run_count} runs found so far)...")
    
        # Only process running activities
        if activity.get('type') != 'Run':
            continue
            
        try:
            activity_date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            distance = activity.get('distance', 0)
            moving_time = activity.get('moving_time', 0)
            elapsed_time = activity.get('elapsed_time', 0)
            elevation_gain = activity.get('total_elevation_gain', 0)
            
            # All time stats
            stats['all_run_totals']['count'] += 1
            stats['all_run_totals']['distance'] += distance
            stats['all_run_totals']['moving_time'] += moving_time
            stats['all_run_totals']['elapsed_time'] += elapsed_time
            stats['all_run_totals']['elevation_gain'] += elevation_gain
            
            # Year to date stats
            if activity_date >= year_start:
                stats['ytd_run_totals']['count'] += 1
                stats['ytd_run_totals']['distance'] += distance
                stats['ytd_run_totals']['moving_time'] += moving_time
                stats['ytd_run_totals']['elapsed_time'] += elapsed_time
                stats['ytd_run_totals']['elevation_gain'] += elevation_gain
            
            # This month stats
            if activity_date >= month_start:
                stats['this_month_run_totals']['count'] += 1
                stats['this_month_run_totals']['distance'] += distance
                stats['this_month_run_totals']['moving_time'] += moving_time
                stats['this_month_run_totals']['elapsed_time'] += elapsed_time
                stats['this_month_run_totals']['elevation_gain'] += elevation_gain
            
            # This week stats
            if activity_date >= week_start:
                stats['this_week_run_totals']['count'] += 1
                stats['this_week_run_totals']['distance'] += distance
                stats['this_week_run_totals']['moving_time'] += moving_time
                stats['this_week_run_totals']['elapsed_time'] += elapsed_time
                stats['this_week_run_totals']['elevation_gain'] += elevation_gain
            
            # Recent (last 4 weeks) stats
            if activity_date >= recent_cutoff:
                stats['recent_run_totals']['count'] += 1
                stats['recent_run_totals']['distance'] += distance
                stats['recent_run_totals']['moving_time'] += moving_time
                stats['recent_run_totals']['elapsed_time'] += elapsed_time
                stats['recent_run_totals']['elevation_gain'] += elevation_gain
                
        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing activity: {e}")
            continue
    
    logger.info(f"✅ Stats calculation complete!")
    logger.info(f"📈 Found {run_count} running activities out of {len(activities)} total activities")
    logger.info(f"🏃 This week: {stats['this_week_run_totals']['count']} runs, {stats['this_week_run_totals']['distance']:.1f}m")
    logger.info(f"📅 This year: {stats['ytd_run_totals']['count']} runs, {stats['ytd_run_totals']['distance']:.1f}m")
    logger.info(f"🏆 All time: {stats['all_run_totals']['count']} runs, {stats['all_run_totals']['distance']:.1f}m")
    
    return stats

@app.route('/api/athlete/stats/enhanced', methods=['GET'])
def get_enhanced_athlete_stats():
    """Get enhanced athlete stats with actual weekly calculations"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        logger.info(f"Enhanced stats request for user_id: {user_id}")
        
        # Get Strava access token from JWT (new format) or database (legacy)
        access_token = None
        if 'access_token' in payload:
            access_token = payload['access_token']
        else:
            token_record = db_service.get_active_token(user_id)
            if not token_record:
                return jsonify({'error': 'No valid Strava token found'}), 401
            access_token = token_record.access_token
        
        if not access_token:
            return jsonify({'error': 'No valid Strava token available'}), 401
        
        # Check if we should use cached stats or refresh from API
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        should_refresh = db_service.should_refresh_calculated_stats(user_id, refresh_interval_hours=6)
        logger.info(f"Cache check for user {user_id}: force_refresh={force_refresh}, should_refresh={should_refresh}")
        
        if not force_refresh and not should_refresh:
            # Use cached stats
            logger.info(f"Using cached stats for user {user_id}")
            cached_stats = db_service.get_cached_stats_as_dict(user_id)
            if cached_stats:
                logger.info(f"Returning cached stats with {cached_stats.get('cache_info', {}).get('total_activities', 0)} activities")
                return jsonify({'stats': cached_stats, 'source': 'database_cache'})
            else:
                logger.warning(f"No cached stats found for user {user_id}, will fetch fresh data")
        
        # Fetch ALL activities and calculate comprehensive stats
        logger.info(f"Refreshing stats for user {user_id} - fetching all activities from Strava")
        all_activities = fetch_all_strava_activities(access_token)
        
        # Calculate comprehensive stats from all activities
        calculated_stats = calculate_comprehensive_stats(all_activities)
        
        # Cache the calculated stats in database
        db_service.update_calculated_stats(user_id, calculated_stats, len(all_activities))
        
        return jsonify({'stats': calculated_stats, 'source': 'calculated_and_cached'})
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error in get_enhanced_athlete_stats: {e}")
        return jsonify({'error': 'Failed to fetch enhanced stats'}), 500

@app.route('/api/athlete/stats/refresh', methods=['POST'])
def refresh_athlete_stats():
    """Force refresh athlete stats from Strava API"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token
        access_token = None
        if 'access_token' in payload:
            access_token = payload['access_token']
        else:
            token_record = db_service.get_active_token(user_id)
            if not token_record:
                return jsonify({'error': 'No valid Strava token found'}), 401
            access_token = token_record.access_token
        
        if not access_token:
            return jsonify({'error': 'No valid Strava token available'}), 401
        
        # Force refresh - fetch ALL activities and recalculate
        logger.info(f"Force refreshing stats for user {user_id}")
        all_activities = fetch_all_strava_activities(access_token)
        calculated_stats = calculate_comprehensive_stats(all_activities)
        
        # Update cache
        db_service.update_calculated_stats(user_id, calculated_stats, len(all_activities))
        
        return jsonify({
            'stats': calculated_stats, 
            'source': 'force_refreshed',
            'activities_processed': len(all_activities),
            'message': f'Successfully refreshed stats from {len(all_activities)} activities'
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error in refresh_athlete_stats: {e}")
        return jsonify({'error': 'Failed to refresh stats'}), 500

@app.route('/api/athlete/stats', methods=['GET'])
def get_athlete_stats():
    """Get athlete's statistics including weekly totals with smart caching"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token from JWT (new format) or database (legacy)
        access_token = None
        if 'access_token' in payload:
            # New format - token is in JWT
            access_token = payload['access_token']
        else:
            # Legacy format - get from database
            user = db_service.get_user(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            token_record = db_service.get_active_token(user_id)
            if not token_record:
                return jsonify({'error': 'No valid Strava token found'}), 401
            access_token = token_record.access_token
        
        if not access_token:
            return jsonify({'error': 'No valid Strava token available'}), 401
        
        # Always fetch fresh stats from Strava API (no caching since no database storage)
        logger.info(f"Fetching stats for user {user_id} from Strava API")
        
        try:
            # Fetch fresh stats from Strava
            fresh_stats = fetch_athlete_stats(access_token, user_id)
            return jsonify({'stats': fresh_stats, 'source': 'strava_api'})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Strava API error: {e}")
            return jsonify({'error': 'Failed to fetch stats from Strava API'}), 500
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error in get_athlete_stats: {e}")
        return jsonify({'error': 'Failed to fetch athlete stats'}), 500

def format_stats_for_response(stats_record):
    """Format database stats record for API response"""
    return {
        'recent_run_totals': {
            'count': stats_record.recent_runs_count,
            'distance': stats_record.recent_runs_distance,
            'moving_time': stats_record.recent_runs_moving_time,
            'elapsed_time': stats_record.recent_runs_elapsed_time,
            'elevation_gain': stats_record.recent_runs_elevation_gain
        },
        'ytd_run_totals': {
            'count': stats_record.ytd_runs_count,
            'distance': stats_record.ytd_runs_distance,
            'moving_time': stats_record.ytd_runs_moving_time,
            'elapsed_time': stats_record.ytd_runs_elapsed_time,
            'elevation_gain': stats_record.ytd_runs_elevation_gain
        },
        'all_run_totals': {
            'count': stats_record.all_runs_count,
            'distance': stats_record.all_runs_distance,
            'moving_time': stats_record.all_runs_moving_time,
            'elapsed_time': stats_record.all_runs_elapsed_time,
            'elevation_gain': stats_record.all_runs_elevation_gain
        }
    }

@app.route('/api/athlete/stats/status', methods=['GET'])
def get_stats_status():
    """Get the status of cached stats for a user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        stats = db_service.get_user_stats(user_id)
        
        if not stats:
            return jsonify({
                'has_cached_data': False,
                'needs_initial_fetch': True,
                'message': 'No cached data available - first fetch required'
            })
        
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        
        # Check if cache is stale (6 hours)
        cache_stale = False
        time_since_fetch = None
        
        if stats.activities_last_fetched:
            # Ensure timezone compatibility
            last_fetched = stats.activities_last_fetched
            if last_fetched.tzinfo is None:
                last_fetched = last_fetched.replace(tzinfo=timezone.utc)
                
            time_since_fetch = now - last_fetched
            cache_stale = time_since_fetch.total_seconds() > (6 * 3600)
        else:
            cache_stale = True
        
        return jsonify({
            'has_cached_data': stats.activities_last_fetched is not None,
            'cache_stale': cache_stale,
            'last_fetched': stats.activities_last_fetched.isoformat() if stats.activities_last_fetched else None,
            'calculated_at': stats.stats_calculated_at.isoformat() if stats.stats_calculated_at else None,
            'total_activities': stats.total_activities_processed or 0,
            'hours_since_fetch': time_since_fetch.total_seconds() / 3600 if time_since_fetch else None,
            'needs_refresh': cache_stale,
            'message': 'Using cached data' if not cache_stale else 'Cache is stale - will refresh on next request'
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error in get_stats_status: {e}")
        return jsonify({'error': 'Failed to get stats status'}), 500

@app.route('/api/activities/<int:activity_id>/grade', methods=['POST'])
def grade_activity(activity_id):
    """Grade an activity against a target shape using Procrustes analysis"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    data = request.get_json()
    if not data or 'shape' not in data:
        return jsonify({'error': 'Shape parameter required'}), 400
    
    shape = data['shape'].lower()
    # Check if detailed visualization data is requested
    include_coordinates = data.get('include_coordinates', False)
    logger.info(f"Grade request - include_coordinates: {include_coordinates}")
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get Strava access token (with automatic refresh if needed)
        if 'access_token' in payload:
            # For JWT tokens, we need to check if they're expired and handle refresh
            access_token = payload['access_token']
            # Try a test request to see if token is still valid
            try:
                test_headers = {'Authorization': f'Bearer {access_token}'}
                test_response = requests.get('https://www.strava.com/api/v3/athlete', headers=test_headers)
                if test_response.status_code == 401:
                    logger.info(f"JWT access token expired for user {user_id} during grading, attempting refresh")
                    # Try to refresh using refresh_token from JWT
                    if 'refresh_token' in payload:
                        new_token_data = refresh_strava_token(payload['refresh_token'])
                        access_token = new_token_data['access_token']
                        # Store the new token in database for future use
                        db_service.store_user_tokens(user_id, new_token_data)
                        logger.info(f"Successfully refreshed JWT token for user {user_id} during grading")
                    else:
                        # Fallback to database token refresh
                        access_token = get_valid_access_token(user_id)
            except Exception as e:
                logger.warning(f"JWT token test failed for user {user_id} during grading: {e}, trying database fallback")
                access_token = get_valid_access_token(user_id)
        else:
            access_token = get_valid_access_token(user_id)
            
        if not access_token:
            return jsonify({
                'error': 'Strava authentication expired', 
                'auth_required': True,
                'message': 'Please reconnect with Strava to grade activities'
            }), 401
        
        # Check if we already have a score for this activity and shape
        existing_score = db_service.get_challenge_score(user_id, str(activity_id), shape)
        if existing_score and not include_coordinates:
            # Only return cached score if visualization data is not requested
            return jsonify({
                'activity_id': activity_id,
                'shape': shape,
                'score': round(existing_score.score, 2),
                'grade': existing_score.letter_grade,
                'message': f'Your run scored {existing_score.score:.1f}% similarity to a {shape}!',
                'cached': True
            })
        
        # Fetch activity streams (GPS data) with token refresh support
        streams = None
        try:
            stream_types = 'latlng,distance,time'
            url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams'
            params = {'keys': stream_types, 'key_by_type': 'true'}
            
            streams = make_strava_request(url, access_token, user_id, params)
        except requests.exceptions.HTTPError as http_err:
            logger.warning(f"Streams API failed for activity {activity_id}: {http_err}; attempting polyline fallback")
            streams = None
        except Exception as e:
            logger.warning(f"Error fetching streams for activity {activity_id}: {e}; attempting polyline fallback")
            streams = None
        
        # Fallback: if no streams/latlng, try decoding the activity's summary polyline
        try:
            if not streams or 'latlng' not in streams or not streams['latlng'].get('data'):
                act = make_strava_request(
                    f'https://www.strava.com/api/v3/activities/{activity_id}',
                    access_token,
                    user_id,
                    {'include_all_efforts': 'false'}
                )
                polyline = None
                if isinstance(act, dict):
                    polyline = (act.get('map') or {}).get('summary_polyline') or (act.get('map') or {}).get('polyline')
                if polyline:
                    coords = decode_polyline(polyline)
                    if coords:
                        streams = streams or {}
                        streams['latlng'] = {'data': coords}
        except requests.HTTPError as http_err:
            logger.warning(f"Streams fallback failed for activity {activity_id}: {http_err}")
        except Exception as e:
            logger.warning(f"Error during polyline fallback for activity {activity_id}: {e}")
        
        if not streams or 'latlng' not in streams or not streams['latlng'].get('data'):
            return jsonify({'error': 'No GPS data available for this activity'}), 400
        
        # Convert streams to the format expected by the shape grader
        import tempfile
        import json
        
        # Create temporary JSON file with GPS data
        gps_data = {
            'coordinates': streams['latlng']['data'],
            'activity_id': activity_id
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(gps_data, temp_file)
            temp_gps_file = temp_file.name
        
        # Determine target shape file
        base_path = '/Users/axeledin/Desktop/ACM_Folder/ACM/in-shape-frontend/public/shapes'
        shape_file_map = {
            'rectangle': f'{base_path}/rectangle-1.svg',
            'circle': f'{base_path}/circle-1.svg',
            'triangle': f'{base_path}/triangle-1.svg',
            'heart': f'{base_path}/heart-1.svg',
            'star': f'{base_path}/star-1.svg'
        }
        
        svg_file = shape_file_map.get(shape)
        if not svg_file or not os.path.exists(svg_file):
            return jsonify({'error': f'Shape "{shape}" not supported or file not found'}), 400
        
        # Import and use the shape grader
        if include_coordinates:
            try:
                from procrustes_shape_grader import grade_shape_similarity_with_transform
                # Calculate similarity score with transformation data
                result = grade_shape_similarity_with_transform(temp_gps_file, svg_file)
                score = result['similarity']
                letter_grade = get_letter_grade(score)
                
                logger.info(f"Enhanced grade result keys: {list(result.keys())}")
                logger.info(f"Strava points count: {len(result.get('strava_transformed', []))}")
                logger.info(f"SVG points count: {len(result.get('svg_normalized', []))}")
                
                # Store the score in the database
                db_service.store_challenge_score(user_id, str(activity_id), shape, score, letter_grade)
                
                # Clean up temporary file
                os.unlink(temp_gps_file)
                
                return jsonify({
                    'activity_id': activity_id,
                    'shape': shape,
                    'score': round(score, 2),
                    'grade': letter_grade,
                    'message': f'Your run scored {score:.1f}% similarity to a {shape}!',
                    'cached': False,
                    'visualization_data': {
                        'strava_transformed': result['strava_transformed'],
                        'svg_normalized': result['svg_normalized'],
                        'transform_info': result['transform_info']
                    }
                })
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_gps_file):
                    os.unlink(temp_gps_file)
                raise e
        else:
            try:
                from procrustes_shape_grader import grade_shape_similarity_procrustes
                # Calculate similarity score only
                score = grade_shape_similarity_procrustes(temp_gps_file, svg_file)
                letter_grade = get_letter_grade(score)
                
                # Store the score in the database
                db_service.store_challenge_score(user_id, str(activity_id), shape, score, letter_grade)
                
                # Clean up temporary file
                os.unlink(temp_gps_file)
                
                return jsonify({
                    'activity_id': activity_id,
                    'shape': shape,
                    'score': round(score, 2),
                    'grade': letter_grade,
                    'message': f'Your run scored {score:.1f}% similarity to a {shape}!',
                    'cached': False
                })
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_gps_file):
                    os.unlink(temp_gps_file)
                raise e
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error grading activity: {e}")
        return jsonify({'error': 'Failed to grade activity'}), 500

def get_letter_grade(score):
    """Convert numeric score to letter grade"""
    if score >= 90:
        return 'A+'
    elif score >= 85:
        return 'A'
    elif score >= 80:
        return 'A-'
    elif score >= 75:
        return 'B+'
    elif score >= 70:
        return 'B'
    elif score >= 65:
        return 'B-'
    elif score >= 60:
        return 'C+'
    elif score >= 55:
        return 'C'
    elif score >= 50:
        return 'C-'
    else:
        return 'F'

@app.route('/debug/jwt', methods=['GET'])
def debug_jwt():
    """Debug endpoint to see JWT contents"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No authorization token'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return jsonify({'jwt_payload': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user and invalidate session"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'No session to logout'}), 200
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Invalidate user sessions in database
        db_service.invalidate_user_sessions(user_id)
        
        logger.info(f"User {user_id} logged out successfully")
        return jsonify({'message': 'Logged out successfully'})
    
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token, considered logged out'}), 200

if __name__ == '__main__':
    # Check for required environment variables
    required_env_vars = ['STRAVA_CLIENT_ID', 'STRAVA_CLIENT_SECRET']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your Strava OAuth app credentials in a .env file")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
