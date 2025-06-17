#!/bin/bash

# Start MinIO with Docker Compose
docker-compose up -d

echo "MinIO started successfully"
echo "Web Console: http://localhost:9001"
echo "API Endpoint: http://localhost:9000"
echo "Username: admin"
echo "Password: minio123456"