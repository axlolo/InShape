"""
Database models for InShape application
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    # Strava athlete ID as primary key
    id = Column(String, primary_key=True)
    
    # Basic profile info
    firstname = Column(String(100))
    lastname = Column(String(100))
    profile_url = Column(Text)
    profile_medium_url = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    sex = Column(String(10))
    
    # Strava account info
    strava_created_at = Column(DateTime)
    premium = Column(Boolean, default=False)
    
    # App metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    stats = relationship("UserStats", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.id}: {self.firstname} {self.lastname}>"

class UserToken(Base):
    __tablename__ = 'user_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Strava OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    token_type = Column(String(20), default='Bearer')
    scope = Column(String(200))
    
    # Token metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def is_expired(self):
        """Check if the access token is expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def __repr__(self):
        return f"<UserToken {self.id}: {self.user_id}>"

class UserStats(Base):
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Recent totals (last 4 weeks)
    recent_runs_count = Column(Integer, default=0)
    recent_runs_distance = Column(Float, default=0.0)  # meters
    recent_runs_moving_time = Column(Integer, default=0)  # seconds
    recent_runs_elapsed_time = Column(Integer, default=0)  # seconds
    recent_runs_elevation_gain = Column(Float, default=0.0)  # meters
    
    # Year-to-date totals
    ytd_runs_count = Column(Integer, default=0)
    ytd_runs_distance = Column(Float, default=0.0)
    ytd_runs_moving_time = Column(Integer, default=0)
    ytd_runs_elapsed_time = Column(Integer, default=0)
    ytd_runs_elevation_gain = Column(Float, default=0.0)
    
    # All-time totals
    all_runs_count = Column(Integer, default=0)
    all_runs_distance = Column(Float, default=0.0)
    all_runs_moving_time = Column(Integer, default=0)
    all_runs_elapsed_time = Column(Integer, default=0)
    all_runs_elevation_gain = Column(Float, default=0.0)
    
    # This week totals (Monday to Sunday)
    this_week_runs_count = Column(Integer, default=0)
    this_week_runs_distance = Column(Float, default=0.0)
    this_week_runs_moving_time = Column(Integer, default=0)
    this_week_runs_elapsed_time = Column(Integer, default=0)
    this_week_runs_elevation_gain = Column(Float, default=0.0)
    
    # This month totals
    this_month_runs_count = Column(Integer, default=0)
    this_month_runs_distance = Column(Float, default=0.0)
    this_month_runs_moving_time = Column(Integer, default=0)
    this_month_runs_elapsed_time = Column(Integer, default=0)
    this_month_runs_elevation_gain = Column(Float, default=0.0)
    
    # Cache metadata
    activities_last_fetched = Column(DateTime)  # When we last fetched all activities
    stats_calculated_at = Column(DateTime)      # When stats were last calculated
    total_activities_processed = Column(Integer, default=0)  # Number of activities in calculation
    
    # Metadata
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="stats")
    
    def __repr__(self):
        return f"<UserStats {self.user_id}: {self.all_runs_count} total runs>"

class Activity(Base):
    __tablename__ = 'activities'
    
    # Strava activity ID as primary key
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Basic activity info
    name = Column(String(200))
    type = Column(String(50))  # Run, Ride, etc.
    sport_type = Column(String(50))
    start_date = Column(DateTime)
    start_date_local = Column(DateTime)
    
    # Activity metrics
    distance = Column(Float)  # meters
    moving_time = Column(Integer)  # seconds
    elapsed_time = Column(Integer)  # seconds
    total_elevation_gain = Column(Float)  # meters
    average_speed = Column(Float)  # m/s
    max_speed = Column(Float)  # m/s
    
    # GPS data (for shape analysis)
    has_gps = Column(Boolean, default=False)
    start_latlng = Column(JSON)  # [lat, lng]
    end_latlng = Column(JSON)  # [lat, lng]
    
    # Shape analysis results
    analyzed_shape = Column(String(50))  # Rectangle, Circle, etc.
    shape_accuracy = Column(Float)  # 0.0 to 1.0
    shape_analysis_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<Activity {self.id}: {self.name}>"

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Session info
    jwt_token_hash = Column(String(64), nullable=False)  # SHA-256 hash of JWT
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now())
    
    # Session metadata
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserSession {self.id}: {self.user_id}>"


class ChallengeScore(Base):
    __tablename__ = 'challenge_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    activity_id = Column(String, nullable=False)
    target_shape = Column(String(50), nullable=False)  # The shape being compared against (rectangle, oval, plus)
    grading_method = Column(String(20), nullable=False, default='iou')  # Now using IoU algorithm
    score = Column(Float, nullable=False)  # Similarity score (0-100)
    letter_grade = Column(String(2), nullable=False)  # A+, A, B+, etc.
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChallengeScore {self.user_id}-{self.activity_id}-{self.target_shape}-{self.grading_method}: {self.score}%>"
