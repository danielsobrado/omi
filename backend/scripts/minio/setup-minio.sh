#!/bin/bash

# MinIO Setup Script for Development
# This script sets up a local MinIO instance for testing the migration

echo "Setting up MinIO for development..."

# Create directories for MinIO data
mkdir -p ./minio-data

# Download MinIO binary if not present
if [ ! -f "./minio" ]; then
    echo "Downloading MinIO binary..."
    wget https://dl.min.io/server/minio/release/linux-amd64/minio
    chmod +x minio
fi

# Start MinIO server in background
echo "Starting MinIO server..."
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin123 ./minio server ./minio-data --console-address ":9001" &

# Wait for MinIO to start
sleep 5

# Install MinIO client if not present
if [ ! -f "./mc" ]; then
    echo "Downloading MinIO client..."
    wget https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
fi

# Configure MinIO client
echo "Configuring MinIO client..."
./mc alias set local http://localhost:9000 minioadmin minioadmin123

# Create the omi-data bucket
echo "Creating omi-data bucket..."
./mc mb local/omi-data

# Set public read policy for development (adjust for production)
./mc anonymous set public local/omi-data

echo "MinIO setup complete!"
echo "MinIO Console: http://localhost:9001"
echo "MinIO API: http://localhost:9000"
echo "Username: minioadmin"
echo "Password: minioadmin123"
echo ""
echo "Add these to your .env file:"
echo "S3_ENDPOINT_URL=http://localhost:9000"
echo "S3_ACCESS_KEY_ID=minioadmin"
echo "S3_SECRET_ACCESS_KEY=minioadmin123"
echo "S3_BUCKET_NAME=omi-data"
