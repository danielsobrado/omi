#!/bin/bash

# Redis startup script for OMI backend

echo "Starting Redis for OMI backend..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Change to the script directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Redis
echo "Starting Redis container..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
sleep 5

# Test Redis connection
echo "Testing Redis connection..."
if [ -n "$REDIS_PASSWORD" ]; then
    docker exec omi-redis redis-cli -a "$REDIS_PASSWORD" ping
else
    docker exec omi-redis redis-cli ping
fi

if [ $? -eq 0 ]; then
    echo "✅ Redis is running successfully!"
    echo "Redis is available at: localhost:6379"
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "Password authentication is enabled"
    else
        echo "No password authentication (development mode)"
    fi
else
    echo "❌ Failed to connect to Redis"
    exit 1
fi
