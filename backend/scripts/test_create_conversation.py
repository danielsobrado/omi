#!/usr/bin/env python3
"""
Test script to create an in-progress conversation in the database and Redis for testing the API
"""
import json
import redis
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the path so we can import the database modules
sys.path.append('/home/sobradod/omi/backend')

# Set environment variables
os.environ['DATABASE_CHOICE'] = 'postgres'

# Import database modules
import database.conversations as conversations_db
import database.redis_db as redis_db

print("Creating test in-progress conversation...")

# Test user ID (from Basic Auth)
uid = "hardcoded_user_01"  # This should match the authenticated user

# Create a test conversation object
conversation_data = {
    "created_at": datetime.now(timezone.utc),
    "started_at": datetime.now(timezone.utc),
    "finished_at": None,
    "transcript_segments": [
        {
            "text": "Hello, this is a test conversation.",
            "speaker": "SPEAKER_00", 
            "start": 0.0,
            "end": 3.0,
            "is_user": False,
            "person_id": None,
            "speaker_id": 0
        },
        {
            "text": "Yes, I can hear you clearly.",
            "speaker": "SPEAKER_01",
            "start": 3.5,
            "end": 6.0,
            "is_user": True,
            "person_id": None,
            "speaker_id": 1
        }
    ],
    "status": "in_progress",
    "language": "en",
    "structured": {
        "title": "",
        "overview": "",
        "emoji": "🧪",
        "category": "other",
        "action_items": [],
        "events": []
    },
    "geolocation": None,
    "photos": [],
    "apps_response": [],
    "discarded": False,
    "visibility": "private",
    "processing_memory_id": None,
    "memory_id": None,
    "type": "conversation",
    "source": "friend"
}

try:
    # Create the conversation in the database
    print("Creating conversation in database...")
    conversation = conversations_db.create_conversation(uid, conversation_data)
    conversation_id = conversation['id']
    print(f"✅ Created conversation in database: {conversation_id}")
    
    # Set the in-progress conversation ID in Redis
    print("Setting in-progress conversation ID in Redis...")
    redis_db.set_in_progress_conversation_id(uid, conversation_id)
    print(f"✅ Set in-progress conversation for user: {uid}")
    
    print(f"\n🎉 SUCCESS! Created in-progress conversation: {conversation_id}")
    print("\nNow you can test with:")
    print("curl -X POST 'http://localhost:8000/v1/conversations' \\")
    print("  -H 'Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==' \\")
    print("  -H 'Content-Type: application/json'")
    
except Exception as e:
    print(f"❌ Failed to create conversation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
