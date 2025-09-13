"""
Database service layer for InShape application
"""

import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from models import Base, User, UserToken, UserStats, Activity, UserSession, ChallengeScore
import hashlib
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, database_url=None):
        """Initialize database connection"""
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///inshape.db')
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self):
        """Close database session"""
        self.SessionLocal.remove()
    
    # User management
    def create_or_update_user(self, strava_athlete_data):
        """Create or update user from Strava athlete data"""
        session = self.get_session()
        try:
            user_id = str(strava_athlete_data['id'])
            
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            
            if user is None:
                # Create new user
                user = User(
                    id=user_id,
                    firstname=strava_athlete_data.get('firstname'),
                    lastname=strava_athlete_data.get('lastname'),
                    profile_url=strava_athlete_data.get('profile'),
                    profile_medium_url=strava_athlete_data.get('profile_medium'),
                    city=strava_athlete_data.get('city'),
                    state=strava_athlete_data.get('state'),
                    country=strava_athlete_data.get('country'),
                    sex=strava_athlete_data.get('sex'),
                    premium=strava_athlete_data.get('premium', False),
                    created_at=datetime.now(timezone.utc),
                    last_login=datetime.now(timezone.utc)
                )
                
                # Parse Strava created_at if available
                if strava_athlete_data.get('created_at'):
                    try:
                        user.strava_created_at = datetime.fromisoformat(
                            strava_athlete_data['created_at'].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                
                session.add(user)
                logger.info(f"Created new user: {user_id}")
            else:
                # Update existing user
                user.firstname = strava_athlete_data.get('firstname', user.firstname)
                user.lastname = strava_athlete_data.get('lastname', user.lastname)
                user.profile_url = strava_athlete_data.get('profile', user.profile_url)
                user.profile_medium_url = strava_athlete_data.get('profile_medium', user.profile_medium_url)
                user.city = strava_athlete_data.get('city', user.city)
                user.state = strava_athlete_data.get('state', user.state)
                user.country = strava_athlete_data.get('country', user.country)
                user.sex = strava_athlete_data.get('sex', user.sex)
                user.premium = strava_athlete_data.get('premium', user.premium)
                user.updated_at = datetime.now(timezone.utc)
                user.last_login = datetime.now(timezone.utc)
                
                logger.info(f"Updated user: {user_id}")
            
            session.commit()
            return user
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating user: {e}")
            raise
        finally:
            session.close()
    
    def get_user(self, user_id):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == str(user_id)).first()
        finally:
            session.close()
    
    # Token management
    def store_user_tokens(self, user_id, token_data):
        """Store or update user's Strava tokens"""
        session = self.get_session()
        try:
            # Deactivate old tokens
            session.query(UserToken).filter(
                and_(UserToken.user_id == str(user_id), UserToken.is_active == True)
            ).update({'is_active': False})
            
            # Create new token record
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', 21600))
            
            token = UserToken(
                user_id=str(user_id),
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_at=expires_at,
                token_type=token_data.get('token_type', 'Bearer'),
                scope=token_data.get('scope', ''),
                is_active=True
            )
            
            session.add(token)
            session.commit()
            
            logger.info(f"Stored tokens for user: {user_id}")
            return token
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing tokens: {e}")
            raise
        finally:
            session.close()
    
    def get_active_token(self, user_id):
        """Get active token for user"""
        session = self.get_session()
        try:
            return session.query(UserToken).filter(
                and_(
                    UserToken.user_id == str(user_id),
                    UserToken.is_active == True,
                    UserToken.expires_at > datetime.now(timezone.utc)
                )
            ).first()
        finally:
            session.close()
    
    def get_latest_token(self, user_id):
        """Get latest token for user (even if expired) for refresh purposes"""
        session = self.get_session()
        try:
            return session.query(UserToken).filter(
                and_(
                    UserToken.user_id == str(user_id),
                    UserToken.is_active == True
                )
            ).order_by(UserToken.created_at.desc()).first()
        finally:
            session.close()
    
    # Stats management
    def update_user_stats(self, user_id, stats_data):
        """Update user statistics from Strava"""
        session = self.get_session()
        try:
            # Check if stats exist
            stats = session.query(UserStats).filter(UserStats.user_id == str(user_id)).first()
            
            if stats is None:
                stats = UserStats(user_id=str(user_id))
                session.add(stats)
            
            # Update recent totals
            if 'recent_run_totals' in stats_data:
                recent = stats_data['recent_run_totals']
                stats.recent_runs_count = recent.get('count', 0)
                stats.recent_runs_distance = recent.get('distance', 0.0)
                stats.recent_runs_moving_time = recent.get('moving_time', 0)
                stats.recent_runs_elapsed_time = recent.get('elapsed_time', 0)
                stats.recent_runs_elevation_gain = recent.get('elevation_gain', 0.0)
            
            # Update YTD totals
            if 'ytd_run_totals' in stats_data:
                ytd = stats_data['ytd_run_totals']
                stats.ytd_runs_count = ytd.get('count', 0)
                stats.ytd_runs_distance = ytd.get('distance', 0.0)
                stats.ytd_runs_moving_time = ytd.get('moving_time', 0)
                stats.ytd_runs_elapsed_time = ytd.get('elapsed_time', 0)
                stats.ytd_runs_elevation_gain = ytd.get('elevation_gain', 0.0)
            
            # Update all-time totals
            if 'all_run_totals' in stats_data:
                all_time = stats_data['all_run_totals']
                stats.all_runs_count = all_time.get('count', 0)
                stats.all_runs_distance = all_time.get('distance', 0.0)
                stats.all_runs_moving_time = all_time.get('moving_time', 0)
                stats.all_runs_elapsed_time = all_time.get('elapsed_time', 0)
                stats.all_runs_elevation_gain = all_time.get('elevation_gain', 0.0)
            
            stats.last_updated = datetime.now(timezone.utc)
            
            session.commit()
            logger.info(f"Updated stats for user: {user_id}")
            return stats
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stats: {e}")
            raise
        finally:
            session.close()
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        session = self.get_session()
        try:
            return session.query(UserStats).filter(UserStats.user_id == str(user_id)).first()
        finally:
            session.close()
    
    def should_update_stats(self, user_id, update_interval_hours=1):
        """Check if user stats should be updated"""
        stats = self.get_user_stats(user_id)
        
        if stats is None or stats.last_updated is None:
            return True
        
        time_since_update = datetime.now(timezone.utc) - stats.last_updated
        return time_since_update.total_seconds() > (update_interval_hours * 3600)
    
    def should_refresh_calculated_stats(self, user_id, refresh_interval_hours=6):
        """Check if calculated stats should be refreshed from activities"""
        stats = self.get_user_stats(user_id)
        
        if stats is None:
            logger.info(f"No stats record found for user {user_id} - needs refresh")
            return True
            
        if stats.activities_last_fetched is None:
            logger.info(f"No activities_last_fetched for user {user_id} - needs refresh")
            return True
        
        # Ensure both datetimes are timezone-aware
        now = datetime.now(timezone.utc)
        last_fetched = stats.activities_last_fetched
        
        # If last_fetched doesn't have timezone info, assume UTC
        if last_fetched.tzinfo is None:
            last_fetched = last_fetched.replace(tzinfo=timezone.utc)
        
        time_since_fetch = now - last_fetched
        hours_since_fetch = time_since_fetch.total_seconds() / 3600
        needs_refresh = time_since_fetch.total_seconds() > (refresh_interval_hours * 3600)
        
        logger.info(f"Cache age for user {user_id}: {hours_since_fetch:.1f} hours (limit: {refresh_interval_hours}h) - needs_refresh: {needs_refresh}")
        return needs_refresh
    
    def update_calculated_stats(self, user_id, calculated_stats, total_activities):
        """Update user statistics with calculated data from activities"""
        session = self.get_session()
        try:
            # Check if stats exist
            stats = session.query(UserStats).filter(UserStats.user_id == str(user_id)).first()
            
            if stats is None:
                stats = UserStats(user_id=str(user_id))
                session.add(stats)
            
            # Update all calculated stats
            stats.this_week_runs_count = calculated_stats['this_week_run_totals']['count']
            stats.this_week_runs_distance = calculated_stats['this_week_run_totals']['distance']
            stats.this_week_runs_moving_time = calculated_stats['this_week_run_totals']['moving_time']
            stats.this_week_runs_elapsed_time = calculated_stats['this_week_run_totals']['elapsed_time']
            stats.this_week_runs_elevation_gain = calculated_stats['this_week_run_totals']['elevation_gain']
            
            stats.this_month_runs_count = calculated_stats['this_month_run_totals']['count']
            stats.this_month_runs_distance = calculated_stats['this_month_run_totals']['distance']
            stats.this_month_runs_moving_time = calculated_stats['this_month_run_totals']['moving_time']
            stats.this_month_runs_elapsed_time = calculated_stats['this_month_run_totals']['elapsed_time']
            stats.this_month_runs_elevation_gain = calculated_stats['this_month_run_totals']['elevation_gain']
            
            stats.ytd_runs_count = calculated_stats['ytd_run_totals']['count']
            stats.ytd_runs_distance = calculated_stats['ytd_run_totals']['distance']
            stats.ytd_runs_moving_time = calculated_stats['ytd_run_totals']['moving_time']
            stats.ytd_runs_elapsed_time = calculated_stats['ytd_run_totals']['elapsed_time']
            stats.ytd_runs_elevation_gain = calculated_stats['ytd_run_totals']['elevation_gain']
            
            stats.all_runs_count = calculated_stats['all_run_totals']['count']
            stats.all_runs_distance = calculated_stats['all_run_totals']['distance']
            stats.all_runs_moving_time = calculated_stats['all_run_totals']['moving_time']
            stats.all_runs_elapsed_time = calculated_stats['all_run_totals']['elapsed_time']
            stats.all_runs_elevation_gain = calculated_stats['all_run_totals']['elevation_gain']
            
            stats.recent_runs_count = calculated_stats['recent_run_totals']['count']
            stats.recent_runs_distance = calculated_stats['recent_run_totals']['distance']
            stats.recent_runs_moving_time = calculated_stats['recent_run_totals']['moving_time']
            stats.recent_runs_elapsed_time = calculated_stats['recent_run_totals']['elapsed_time']
            stats.recent_runs_elevation_gain = calculated_stats['recent_run_totals']['elevation_gain']
            
            # Update cache metadata
            stats.activities_last_fetched = datetime.now(timezone.utc)
            stats.stats_calculated_at = datetime.now(timezone.utc)
            stats.total_activities_processed = total_activities
            stats.last_updated = datetime.now(timezone.utc)
            
            session.commit()
            logger.info(f"Updated calculated stats for user: {user_id} ({total_activities} activities)")
            return stats
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating calculated stats: {e}")
            raise
        finally:
            session.close()
    
    def get_cached_stats_as_dict(self, user_id):
        """Get cached stats in the format expected by the frontend"""
        stats = self.get_user_stats(user_id)
        
        if not stats:
            logger.warning(f"No stats record found for user {user_id}")
            return None
            
        logger.info(f"Retrieved cached stats for user {user_id}: last_fetched={stats.activities_last_fetched}, total_activities={stats.total_activities_processed}")
        
        return {
            'this_week_run_totals': {
                'count': stats.this_week_runs_count,
                'distance': stats.this_week_runs_distance,
                'moving_time': stats.this_week_runs_moving_time,
                'elapsed_time': stats.this_week_runs_elapsed_time,
                'elevation_gain': stats.this_week_runs_elevation_gain
            },
            'this_month_run_totals': {
                'count': stats.this_month_runs_count,
                'distance': stats.this_month_runs_distance,
                'moving_time': stats.this_month_runs_moving_time,
                'elapsed_time': stats.this_month_runs_elapsed_time,
                'elevation_gain': stats.this_month_runs_elevation_gain
            },
            'ytd_run_totals': {
                'count': stats.ytd_runs_count,
                'distance': stats.ytd_runs_distance,
                'moving_time': stats.ytd_runs_moving_time,
                'elapsed_time': stats.ytd_runs_elapsed_time,
                'elevation_gain': stats.ytd_runs_elevation_gain
            },
            'all_run_totals': {
                'count': stats.all_runs_count,
                'distance': stats.all_runs_distance,
                'moving_time': stats.all_runs_moving_time,
                'elapsed_time': stats.all_runs_elapsed_time,
                'elevation_gain': stats.all_runs_elevation_gain
            },
            'recent_run_totals': {
                'count': stats.recent_runs_count,
                'distance': stats.recent_runs_distance,
                'moving_time': stats.recent_runs_moving_time,
                'elapsed_time': stats.recent_runs_elapsed_time,
                'elevation_gain': stats.recent_runs_elevation_gain
            },
            'cache_info': {
                'last_fetched': stats.activities_last_fetched.isoformat() if stats.activities_last_fetched else None,
                'calculated_at': stats.stats_calculated_at.isoformat() if stats.stats_calculated_at else None,
                'total_activities': stats.total_activities_processed
            }
        }
    
    def get_challenge_score(self, user_id: str, activity_id: str, target_shape: str):
        """Get existing challenge score for a specific activity, target shape, and grading method"""
        session = self.get_session()
        try:
            score = session.query(ChallengeScore).filter(
                and_(
                    ChallengeScore.user_id == user_id,
                    ChallengeScore.activity_id == activity_id,
                    ChallengeScore.target_shape == target_shape,
                    ChallengeScore.grading_method == 'iou'
                )
            ).first()
            return score
        except Exception as e:
            logger.error(f"Error getting challenge score: {e}")
            return None
        finally:
            session.close()
    
    def store_challenge_score(self, user_id: str, activity_id: str, target_shape: str, score: float, letter_grade: str):
        """Store or update a challenge score"""
        session = self.get_session()
        try:
            # Check if score already exists for this method
            existing_score = session.query(ChallengeScore).filter(
                and_(
                    ChallengeScore.user_id == user_id,
                    ChallengeScore.activity_id == activity_id,
                    ChallengeScore.target_shape == target_shape,
                    ChallengeScore.grading_method == 'iou'
                )
            ).first()
            
            if existing_score:
                # Update existing score
                existing_score.score = score
                existing_score.letter_grade = letter_grade
                existing_score.updated_at = datetime.now(timezone.utc)
                logger.info(f"Updated challenge score for user {user_id}, activity {activity_id}, target_shape {target_shape}, method iou: {score}%")
            else:
                # Create new score record
                new_score = ChallengeScore(
                    user_id=user_id,
                    activity_id=activity_id,
                    target_shape=target_shape,
                    grading_method='iou',
                    score=score,
                    letter_grade=letter_grade
                )
                session.add(new_score)
                logger.info(f"Created new challenge score for user {user_id}, activity {activity_id}, target_shape {target_shape}, method iou: {score}%")
            
            session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing challenge score: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_user_challenge_scores(self, user_id: str, limit: int = 50):
        """Get recent challenge scores for a user"""
        session = self.get_session()
        try:
            scores = session.query(ChallengeScore).filter(
                ChallengeScore.user_id == user_id
            ).order_by(ChallengeScore.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'activity_id': score.activity_id,
                    'target_shape': score.target_shape,
                    'score': score.score,
                    'letter_grade': score.letter_grade,
                    'created_at': score.created_at.isoformat() if score.created_at else None
                }
                for score in scores
            ]
        except Exception as e:
            logger.error(f"Error getting user challenge scores: {e}")
            return []
        finally:
            session.close()
    
    # Session management
    def create_user_session(self, user_id, jwt_token, expires_at, ip_address=None, user_agent=None):
        """Create user session record"""
        session = self.get_session()
        try:
            # Hash the JWT token for security
            token_hash = hashlib.sha256(jwt_token.encode()).hexdigest()
            
            user_session = UserSession(
                user_id=str(user_id),
                jwt_token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            session.add(user_session)
            session.commit()
            
            return user_session
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating session: {e}")
            raise
        finally:
            session.close()
    
    def invalidate_user_sessions(self, user_id):
        """Invalidate all user sessions"""
        session = self.get_session()
        try:
            session.query(UserSession).filter(
                and_(UserSession.user_id == str(user_id), UserSession.is_active == True)
            ).update({'is_active': False})
            
            session.commit()
            logger.info(f"Invalidated sessions for user: {user_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error invalidating sessions: {e}")
            raise
        finally:
            session.close()

# Global database service instance
db_service = DatabaseService()
