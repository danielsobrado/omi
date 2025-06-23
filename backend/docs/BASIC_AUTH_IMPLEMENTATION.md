# Basic Authentication Implementation - Complete

## Overview

The Firebase token verification has been successfully replaced with a simple username/password system managed through environment variables. This implementation provides a temporary authentication solution for development and testing.

## What Was Changed

### 1. Environment Variables (`.env`)
Added the following variables to your `.env` file:
```env
# Basic Auth Credentials (Temporary)
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your_super_secret_password_here
BASIC_AUTH_UID=hardcoded_user_01
```

### 2. Authentication Middleware (`utils/other/endpoints.py`)
- **Removed**: Firebase Admin SDK dependencies
- **Added**: HTTP Basic Authentication logic
- **Modified**: `get_current_user_uid()` function to validate Basic Auth headers
- **Updated**: `delete_account()` to use PostgreSQL instead of Firebase

### 3. Main Application (`main.py`)
- **Removed**: Firebase Admin SDK initialization
- **Removed**: Routers that depend on Firebase (`custom_auth`, `oauth`)
- **Added**: APScheduler for background tasks (replacing Modal cron)
- **Updated**: Simplified startup without Firebase dependencies

### 4. Database Setup
- **Created**: `scripts/seed_user.py` to create the basic auth user in PostgreSQL
- **Updated**: PostgreSQL configuration to use the correct database credentials
- **Fixed**: Database initialization to work with the existing PostgreSQL container

### 5. Dependencies
- **Added**: `apscheduler==3.10.4` to requirements.txt
- **Maintained**: All existing dependencies except Firebase Admin SDK usage

## How to Use

### 1. Database Setup
First, ensure your PostgreSQL database is initialized and the user is created:

```bash
# Initialize the database tables
cd /home/sobradod/omi/backend
POSTGRES_URL="postgresql://unspsc:unspsc@localhost:5433/unspsc" python -c "from database.postgres.init_db import init_database; init_database()"

# Create the basic auth user
python scripts/seed_user.py
```

### 2. Starting the Server
```bash
cd /home/sobradod/omi/backend
DATABASE_CHOICE=postgres POSTGRES_URL="postgresql://unspsc:unspsc@localhost:5433/unspsc" uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Making API Requests

#### Using curl:
```bash
# Valid credentials
curl -u "admin:your_super_secret_password_here" http://localhost:8000/v1/users/people

# Invalid credentials (will return 401)
curl -u "wrong:password" http://localhost:8000/v1/users/people
```

#### Using Python requests:
```python
import requests
from requests.auth import HTTPBasicAuth

# Valid authentication
auth = HTTPBasicAuth('admin', 'your_super_secret_password_here')
response = requests.get('http://localhost:8000/v1/users/people', auth=auth)
print(response.json())

# Invalid authentication (will return 401)
auth = HTTPBasicAuth('wrong', 'password')
response = requests.get('http://localhost:8000/v1/users/people', auth=auth)
print(response.status_code)  # 401
```

#### Using JavaScript/fetch:
```javascript
// Encode credentials for Basic Auth
const credentials = btoa('admin:your_super_secret_password_here');

fetch('http://localhost:8000/v1/users/people', {
    headers: {
        'Authorization': `Basic ${credentials}`
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

## Security Considerations

**⚠️ Important Security Notes:**

1. **Change the default password**: Update `BASIC_AUTH_PASSWORD` in your `.env` file to a strong, unique password
2. **HTTPS only in production**: Basic Auth credentials are base64 encoded (not encrypted), so always use HTTPS in production
3. **Environment security**: Keep your `.env` file secure and never commit it to version control
4. **Temporary solution**: This is designed as a temporary replacement - consider implementing proper OAuth 2.0 or JWT authentication for production use

## Testing the Implementation

A test script is available to verify the authentication:

```bash
cd /home/sobradod/omi/backend
python test_auth.py
```

A minimal test server is also available:
```bash
cd /home/sobradod/omi/backend
python main_test.py
```

## User Database

The system creates a user record in PostgreSQL with:
- **UID**: `hardcoded_user_01` (from `BASIC_AUTH_UID`)
- **Email**: `admin@example.com` (derived from username)
- **Display Name**: `Admin` (capitalized username)

## Admin Key Fallback

The system still supports the existing admin key authentication for backward compatibility:
```bash
curl -H "Authorization: Bearer test<user_id>" http://localhost:8000/v1/users/people
```

## Troubleshooting

### Common Issues:

1. **"Basic Auth environment variables not set"**
   - Ensure your `.env` file contains all three basic auth variables
   - Verify the `.env` file is in the correct directory

2. **Database connection errors**
   - Verify PostgreSQL container is running: `sudo docker ps | grep postgres`
   - Check the database URL in `.env` matches your container configuration

3. **"401 Unauthorized" errors**
   - Verify credentials are correct
   - Ensure you're using Basic Auth format: `Basic <base64-encoded-credentials>`

4. **Import errors**
   - Some routers depend on Firebase and may need additional fixes for full functionality
   - Use the test server (`main_test.py`) for authentication testing

## Next Steps

1. **Update client applications** to use Basic Authentication instead of Firebase tokens
2. **Implement proper password hashing** for production use
3. **Add user management endpoints** for creating/updating users
4. **Consider migrating to JWT tokens** for better scalability and security
5. **Complete PostgreSQL implementation** for all database operations

## Files Modified

- ✅ `.env` - Added basic auth credentials
- ✅ `utils/other/endpoints.py` - Replaced Firebase auth with Basic Auth
- ✅ `main.py` - Removed Firebase dependencies
- ✅ `requirements.txt` - Added APScheduler
- ✅ `scripts/seed_user.py` - Created user seeding script
- ✅ `database/conversations.py` - Fixed database selection logic

## Test Results

✅ **Authentication Test Passed**
- Valid credentials return HTTP 200 with correct user ID
- Invalid credentials return HTTP 401 with appropriate error message  
- Missing credentials return HTTP 401 with appropriate error message
- User successfully created in PostgreSQL database
- Basic Auth header parsing working correctly

The implementation is **complete and functional** for the basic authentication requirements!
