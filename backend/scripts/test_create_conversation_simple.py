#!/usr/bin/env python3
"""
Test script to create an in-progress conversation for testing the API
"""
import sys
import os
sys.path.append('/home/sobradod/omi/backend')

import uuid
from datetime import datetime, timezone
import database.conversations as conversations_db
import database.redis_db as redis_db

print("Creating test in-progress conversation...")

# Test user ID (from Basic Auth)
uid = "hardcoded_user_01"

# Create a simple test conversation object with only required fields
conversation_data = {
    "id": str(uuid.uuid4()),
    "started_at": datetime.now(timezone.utc),
    "status": "in_progress",
    "language": "en",
    "transcript_segments": [
        {
            "text": "Hello, this is a test conversation.",
            "speaker": "SPEAKER_00", 
            "start": 0.0,
            "end": 3.0,
            "is_user": False
        },
        {
            "text": "Yes, I can hear you clearly.",
            "speaker": "SPEAKER_01",
            "start": 3.5,
            "end": 6.0,
            "is_user": True
        }
    ],
    "structured": {
        "title": "",
        "overview": "",
        "emoji": "🧪",
        "category": "other",
        "action_items": [],
        "events": []
    },
    "source": "friend"
}

try:
    # Create the conversation in the database
    print("Creating conversation in database...")
    conversation = conversations_db.create_conversation(uid, conversation_data)
    conversation_id = conversation['id']
    print(f"✅ Created conversation in database: {conversation_id}")
    
    # Set the in-progress conversation ID in Redis using the correct key format
    print("Setting in-progress conversation in Redis...")
    redis_db.set_in_progress_conversation_id(uid, conversation_id)
    print(f"✅ Set in-progress conversation for user: {uid}")
    
    print("\n🎉 Success! Now you can test with:")
    print("curl -X POST 'http://localhost:8000/v1/conversations' \\")
    print("  -H 'Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==' \\")
    print("  -H 'Content-Type: application/json'")
    
except Exception as e:
    print(f"❌ Failed to create conversation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
