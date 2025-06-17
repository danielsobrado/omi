# backend/migration/add_user_notification_fields.py
"""
Migration to add fcm_token and time_zone fields to the users table.
This migration ensures compatibility with notification functionality.
"""

import os
import sys
from sqlalchemy import text

# Add the parent directory to the path to import database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres.client import engine


def migrate_add_user_notification_fields():
    """Add fcm_token and time_zone columns to users table if they don't exist."""
    
    print("Starting migration: add_user_notification_fields")
    
    with engine.connect() as conn:
        # Check if the columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('fcm_token', 'time_zone');
        """))
        
        existing_columns = [row[0] for row in result]
        
        # Add fcm_token column if it doesn't exist
        if 'fcm_token' not in existing_columns:
            print("Adding fcm_token column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN fcm_token VARCHAR;
            """))
            print("✓ fcm_token column added successfully")
        else:
            print("✓ fcm_token column already exists")
        
        # Add time_zone column if it doesn't exist
        if 'time_zone' not in existing_columns:
            print("Adding time_zone column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN time_zone VARCHAR DEFAULT 'UTC';
            """))
            print("✓ time_zone column added successfully")
        else:
            print("✓ time_zone column already exists")
        
        # Commit the transaction
        conn.commit()
    
    print("Migration completed successfully: add_user_notification_fields")


if __name__ == "__main__":
    migrate_add_user_notification_fields()
