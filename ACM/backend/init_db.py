#!/usr/bin/env python3
"""
Database initialization script for InShape application
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import text

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_service
from models import Base

def init_database():
    """Initialize the database with tables"""
    print("🗄️  Initializing InShape database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=db_service.engine)
        print("✅ Database tables created successfully!")
        
        # Test database connection
        session = db_service.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        print("✅ Database connection test successful!")
        
        print(f"📍 Database location: {db_service.engine.url}")
        print("🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

def reset_database():
    """Reset the database (drop and recreate all tables)"""
    print("⚠️  Resetting InShape database...")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=db_service.engine)
        print("🗑️  Dropped existing tables")
        
        # Recreate all tables
        Base.metadata.create_all(bind=db_service.engine)
        print("✅ Recreated database tables")
        
        print("🎉 Database reset complete!")
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        sys.exit(1)

def migrate_database():
    """Migrate database to add new columns for calculated stats"""
    print("🔄 Migrating InShape database...")
    
    try:
        # Create all tables (this will add new columns if they don't exist)
        Base.metadata.create_all(bind=db_service.engine)
        print("✅ Database migration complete!")
        
        # Test database connection
        session = db_service.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        print("✅ Database connection test successful!")
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        sys.exit(1)

def show_stats():
    """Show database statistics"""
    print("📊 Database Statistics:")
    
    try:
        session = db_service.get_session()
        
        # Count users
        from models import User, UserStats, UserToken, UserSession
        
        user_count = session.query(User).count()
        stats_count = session.query(UserStats).count()
        token_count = session.query(UserToken).count()
        session_count = session.query(UserSession).count()
        
        print(f"👥 Users: {user_count}")
        print(f"📈 User Stats Records: {stats_count}")
        print(f"🔑 Active Tokens: {token_count}")
        print(f"🔐 Active Sessions: {session_count}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "reset":
            reset_database()
        elif command == "migrate":
            migrate_database()
        elif command == "stats":
            show_stats()
        elif command == "init":
            init_database()
        else:
            print("Usage: python init_db.py [init|reset|migrate|stats]")
            print("  init    - Initialize database tables")
            print("  reset   - Drop and recreate all tables")
            print("  migrate - Migrate database to add new columns")
            print("  stats   - Show database statistics")
    else:
        init_database()
