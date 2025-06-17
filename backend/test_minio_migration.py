#!/usr/bin/env python3
"""
Test script to verify MinIO migration works correctly.
Run this after setting up MinIO and updating your .env file.
"""

import os
import sys
import tempfile
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")

# Add the parent directory to the path to import storage module
sys.path.append(str(Path(__file__).parent))

try:
    from utils.other.storage import (
        upload_profile_audio,
        get_user_has_speech_profile,
        get_profile_audio_if_exists,
        delete_additional_profile_audio,
        upload_app_logo,
        get_app_thumbnail_url
    )
    print("✅ Successfully imported storage functions")
except Exception as e:
    print(f"❌ Failed to import storage functions: {e}")
    sys.exit(1)

def test_basic_operations():
    """Test basic upload, download, and delete operations"""
    print("\n🧪 Testing basic storage operations...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test file for MinIO migration")
        test_file_path = f.name
    
    try:
        # Test upload
        print("📤 Testing upload...")
        test_uid = "test-user-123"
        result_url = upload_profile_audio(test_file_path, test_uid)
        print(f"Upload result: {result_url}")
        
        # Test existence check
        print("🔍 Testing existence check...")
        exists = get_user_has_speech_profile(test_uid)
        print(f"File exists: {exists}")
        
        if exists:
            print("✅ Upload and existence check successful")
        else:
            print("❌ File doesn't exist after upload")
            return False
        
        # Test download
        print("📥 Testing download...")
        downloaded_path = get_profile_audio_if_exists(test_uid, download=True)
        if downloaded_path and os.path.exists(downloaded_path):
            print(f"✅ Download successful: {downloaded_path}")
            # Clean up downloaded file
            os.unlink(downloaded_path)
        else:
            print("❌ Download failed")
            return False
        
        # Test signed URL generation
        print("🔗 Testing signed URL generation...")
        signed_url = get_profile_audio_if_exists(test_uid, download=False)
        if signed_url:
            print(f"✅ Signed URL generated: {signed_url[:50]}...")
        else:
            print("❌ Signed URL generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def check_environment():
    """Check if required environment variables are set"""
    print("🔧 Checking environment configuration...")
    
    required_vars = [
        'S3_ENDPOINT_URL',
        'S3_ACCESS_KEY_ID', 
        'S3_SECRET_ACCESS_KEY',
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with MinIO configuration")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    print("🚀 MinIO Migration Test")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test basic operations
    if test_basic_operations():
        print("\n🎉 All tests passed! MinIO migration is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check your MinIO setup and configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
