#!/usr/bin/env python3
"""
Test script for the new Basic Authentication system
"""

import base64
import requests
import sys

def test_basic_auth():
    """Test the basic authentication endpoint"""
    
    # Test credentials from .env
    username = "admin"
    password = "your_super_secret_password_here"
    
    # Encode credentials for Basic Auth
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Test URL - we'll use a protected endpoint
    url = "http://localhost:8000/protected"
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    try:
        print("Testing Basic Authentication...")
        print(f"URL: {url}")
        print(f"Username: {username}")
        print(f"Credentials: Basic {encoded_credentials}")
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Basic Authentication is working!")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_auth():
    """Test with invalid credentials"""
    
    # Test with wrong credentials
    credentials = "wrong:password"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    url = "http://localhost:8000/protected"
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    try:
        print("\nTesting with invalid credentials...")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Invalid credentials correctly rejected!")
            return True
        else:
            print("❌ Invalid credentials were accepted (this is bad)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_auth()
    if success:
        test_invalid_auth()
    else:
        sys.exit(1)
