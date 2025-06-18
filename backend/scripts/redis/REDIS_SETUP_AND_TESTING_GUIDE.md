# OMI Backend PostgreSQL Testing Guide

This guide explains how to set up and test the OMI backend with PostgreSQL database backend, including Redis for session management.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with virtual environment
- curl or Postman for API testing
- Git (for cloning the repository)

## Setup Instructions

### 1. Environment Setup

#### Clone and Navigate to Backend
```bash
cd /path/to/omi/backend
```

#### Activate Virtual Environment
```bash
source .venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Configuration

#### Configure Environment Variables
Edit the `.env` file to use PostgreSQL:

```bash
# Database Configuration
DATABASE_CHOICE=postgres
POSTGRES_URL=postgresql://unspsc:unspsc@localhost:5433/unspsc

# Basic Auth Credentials
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your_super_secret_password_here

# Redis Configuration (local)
REDIS_URL=redis://localhost:6379
```

### 3. Start Required Services

#### Start PostgreSQL Database
Ensure your PostgreSQL database is running and accessible at the configured URL.

#### Start Redis (Local Development)
```bash
cd backend/scripts/redis
./start-redis.sh
```

This will:
- Start a Redis container on port 6379
- Create persistent data volume
- Test the connection

#### Alternative: Manual Redis Docker
```bash
cd backend/scripts/redis
docker-compose up -d
```

### 4. Start the OMI Backend Server

```bash
cd backend
source .venv/bin/activate
DATABASE_CHOICE=postgres uvicorn main:app --reload --env-file .env --port 8000
```

## API Testing

### Authentication

All API endpoints require Basic Authentication. Use these credentials:
- Username: `admin`
- Password: `your_super_secret_password_here`

#### Generate Auth Header
```bash
# Base64 encode credentials
echo -n "admin:your_super_secret_password_here" | base64
# Result: YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==
```

### Basic Health Check

```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "modal_services",
  "ml_dependencies_available": true,
  "dependencies_needed": null
}
```

### Test Conversation Endpoints

#### 1. Get Conversations (List)
```bash
curl -X GET \
  "http://localhost:8000/v1/conversations?limit=10&offset=0&statuses=processing,completed&include_discarded=false" \
  -H "accept: application/json" \
  -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ=="
```

Expected response:
```json
[]
```
(Empty array for new installation)

#### 2. Start In-Progress Conversation
```bash
curl -X POST \
  "http://localhost:8000/v1/conversations" \
  -H "accept: application/json" \
  -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
  -H "Content-Type: application/json" \
  -d "{}"
```

This endpoint starts a new conversation session.

#### 3. Get In-Progress Conversation
```bash
curl -X GET \
  "http://localhost:8000/v1/conversations/in-progress" \
  -H "accept: application/json" \
  -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ=="
```

#### 4. Complete In-Progress Conversation
```bash
curl -X POST \
  "http://localhost:8000/v1/conversations/finish" \
  -H "accept: application/json" \
  -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### Test Memory Endpoints

#### Get Memories
```bash
curl -X GET \
  "http://localhost:8000/v1/memories?limit=10&offset=0" \
  -H "accept: application/json" \
  -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ=="
```

### API Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: Missing database functions or import errors
**Solution**: Ensure all PostgreSQL implementation files have the required functions implemented as placeholders.

#### 2. Redis Connection Errors
**Problem**: `redis.exceptions.ConnectionError`
**Solution**: 
- Ensure Redis is running: `docker ps | grep redis`
- Check Redis logs: `docker logs omi-redis`
- Restart Redis: `cd scripts/redis && docker-compose restart`

#### 3. Authentication Errors
**Problem**: `{"detail":"Invalid username or password"}`
**Solution**: 
- Verify credentials in `.env` file
- Check Base64 encoding is correct
- Ensure Authorization header format: `Basic <base64-encoded-credentials>`

#### 4. Database Connection Errors
**Problem**: PostgreSQL connection failed
**Solution**:
- Verify PostgreSQL is running
- Check connection string in `.env`
- Ensure database and user exist

#### 5. Server Won't Start
**Problem**: Various import or configuration errors
**Solution**:
- Check virtual environment is activated
- Install missing packages: `pip install <package-name>`
- Review server logs for specific error messages

### Service Status Checks

#### Check Running Services
```bash
# Check if Redis is running
docker ps | grep redis

# Check if backend server is running
ps aux | grep uvicorn

# Test Redis connection directly
docker exec omi-redis redis-cli ping
```

#### Server Logs
Monitor server logs for errors:
```bash
# If running in foreground, logs appear in terminal
# If running in background, check Docker logs for services
docker logs omi-redis
```

## Development Notes

### Currently Disabled Features

Due to missing PostgreSQL implementations, the following routers are temporarily disabled:
- `/apps/*` - Applications and personas management
- `/payment/*` - Payment processing

### External Services

The following external services show warnings but don't prevent basic functionality:
- **VAD (Voice Activity Detection)**: Model download fails due to network restrictions
- **Google Cloud Translation**: Missing credentials file
- **Typesense Search**: No configuration provided

### Database Schema

The PostgreSQL implementation uses SQLAlchemy models defined in:
- `backend/database/postgres/models.py`
- Tables are automatically created on startup

## Testing Workflow

### Complete Testing Sequence

1. **Setup Environment**
   ```bash
   cd backend
   source .venv/bin/activate
   cd scripts/redis && ./start-redis.sh && cd ../..
   ```

2. **Start Server**
   ```bash
   DATABASE_CHOICE=postgres uvicorn main:app --reload --env-file .env --port 8000
   ```

3. **Test Health**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Test Authentication**
   ```bash
   curl -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
        http://localhost:8000/v1/conversations
   ```

5. **Test Conversation Flow**
   ```bash
   # Start conversation
   curl -X POST -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
        -H "Content-Type: application/json" \
        http://localhost:8000/v1/conversations -d "{}"
   
   # Check in-progress
   curl -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
        http://localhost:8000/v1/conversations/in-progress
   
   # Finish conversation
   curl -X POST -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
        -H "Content-Type: application/json" \
        http://localhost:8000/v1/conversations/finish -d "{}"
   
   # List conversations
   curl -H "Authorization: Basic YWRtaW46eW91cl9zdXBlcl9zZWNyZXRfcGFzc3dvcmRfaGVyZQ==" \
        "http://localhost:8000/v1/conversations?limit=10"
   ```

## Success Criteria

✅ **Server Starts Successfully**
- No fatal import errors
- Database connections established
- Redis connection working

✅ **Basic API Functionality**
- Health endpoint responds
- Authentication works
- Conversation endpoints respond (even if empty)

✅ **Database Integration**
- PostgreSQL tables created
- Basic CRUD operations work
- Session management via Redis

## Next Steps for Production

1. **Complete PostgreSQL Implementation**
   - Implement missing functions in apps and users modules
   - Add proper data validation and error handling

2. **External Service Configuration**
   - Set up Google Cloud credentials for translation
   - Configure Typesense for search functionality
   - Set up VAD service or use local models

3. **Security Hardening**
   - Replace basic auth with proper JWT authentication
   - Add rate limiting and request validation
   - Configure HTTPS and CORS properly

4. **Monitoring and Logging**
   - Add structured logging
   - Set up health checks and metrics
   - Configure error tracking
