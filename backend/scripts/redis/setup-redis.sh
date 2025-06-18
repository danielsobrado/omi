#!/bin/bash

# Redis Setup Script for OMI Backend Development
# This script sets up a local Redis instance using Docker

echo "Setting up Redis for OMI backend development..."

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

# Pull Redis image
echo "Pulling Redis Docker image..."
docker pull redis:7-alpine

# Create Redis volume if it doesn't exist
echo "Creating Redis data volume..."
docker volume create redis_data 2>/dev/null || true

echo "Redis setup completed!"
echo "You can now start Redis using: ./start-redis.sh"
echo "Or manually with: docker-compose up -d"
