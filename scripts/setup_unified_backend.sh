#!/bin/bash

# Omi Backend Modal Migration Setup Script
# This script helps you migrate from Modal to a unified local FastAPI application

set -e

echo "🚀 Omi Backend Modal Migration Setup"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "routers" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

echo "📋 Step 1: Creating environment configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ Created .env file. Please edit it with your configuration values."
else
    echo "ℹ️  .env file already exists. Skipping creation."
fi

echo ""
echo "📋 Step 2: Installing dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "📋 Step 3: Creating necessary directories..."

# Create required directories
mkdir -p _temp _samples _segments _speech_profiles

echo ""
echo "📋 Step 4: Checking ML model requirements..."

echo "ℹ️  The unified backend includes heavy ML models that will be downloaded on first use:"
echo "   - SpeechBrain ECAPA-VOXCELEB for speaker identification"
echo "   - PyAnnote Voice Activity Detection"
echo "   These models require GPU for optimal performance but can run on CPU."

echo ""
echo "🎉 Migration setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit your .env file with the correct values"
echo "2. Ensure your database is running and accessible"
echo "3. Run the application:"
echo ""
echo "   For development:"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "   For production with Docker:"
echo "   docker build -f Dockerfile.unified -t omi-backend ."
echo "   docker run -p 8080:8080 --env-file .env --gpus all omi-backend"
echo ""
echo "🔧 The application will be available at: http://localhost:8080"
echo "📖 API documentation: http://localhost:8080/docs"
echo ""
echo "✨ Modal endpoints have been migrated to:"
echo "   - /v1/speaker-identification (was Modal speech_profile)"
echo "   - /v1/vad (was Modal VAD)"
echo "   - Cron jobs now run with APScheduler"
echo ""
echo "🗑️  You can now safely remove these files:"
echo "   - modal/ directory"
echo "   - pusher/ directory"
