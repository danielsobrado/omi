# Development Environment Setup

## Prerequisites

### Common Tools
- **Git**: Version control
- **FFmpeg**: Audio/video processing
- **Opus**: Audio codec
- **Node.js**: 19+ for documentation
- **Python**: 3.9+ for backend
- **Docker**: For containerized development

### Mobile App Development
- **Flutter SDK**: 3.32.4+
- **Dart SDK**: 3.0+
- **Android Studio**: Iguana 2024.3+
- **Xcode**: 16.4+ (iOS development)
- **CocoaPods**: 1.16.2+
- **JDK**: 21
- **Gradle**: 8.10+
- **NDK**: 27.0.12077973

### Firmware Development
- **nRF Connect for VS Code**: Nordic development environment
- **CMake**: Build system
- **nRF Connect SDK**: Nordic SDK
- **J-Link**: For debugging (optional)

### Backend Development
- **Python Virtual Environment**: For dependency isolation
- **PostgreSQL**: Database (optional, can use Firestore)
- **Redis**: Caching
- **Google Cloud SDK**: For GCP integration
- **ngrok**: For local development tunneling

## Environment Configuration

### Backend (.env file)
```env
# Database
DATABASE_CHOICE=postgres  # or firestore
POSTGRES_URL=postgresql://user:password@localhost:5432/db

# Redis
REDIS_DB_HOST=localhost
REDIS_DB_PORT=6379

# API Keys
OPENAI_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Admin
ADMIN_KEY=development_key
```

### Mobile App (.dev.env)
```env
API_BASE_URL=https://your-backend-url.com
```

### Firebase Setup
- Enable Cloud Resource Manager API
- Enable Firebase Management API
- Enable Cloud Firestore API
- Setup authentication with gcloud

## Development Workflow

### Backend
1. Activate virtual environment
2. Install dependencies
3. Setup environment variables
4. Run database migrations
5. Start development server

### Mobile App
1. Run platform-specific setup script
2. Install dependencies
3. Build and run on device/emulator

### Firmware
1. Open project in nRF Connect for VS Code
2. Select appropriate board configuration
3. Build firmware
4. Flash to device

## Common Issues

### Backend
- SSL certificate issues with model downloads
- Database connection failures
- Missing API keys
- Port conflicts

### Mobile App
- Platform-specific build issues
- Missing provisioning profiles (iOS)
- Bluetooth permission issues
- Flutter version compatibility

### Firmware
- Missing nRF Connect SDK
- Board configuration errors
- Flashing failures
- Hardware compatibility issues