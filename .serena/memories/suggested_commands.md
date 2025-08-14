# Suggested Commands

## Windows System Commands
- `dir` - List directory contents
- `cd` - Change directory
- `copy` - Copy files
- `move` - Move files
- `del` - Delete files
- `findstr` - Search for text in files
- `git` - Version control operations

## Backend Development
```bash
# Setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Development
uvicorn main:app --reload --env-file .env
python -m pytest  # Run tests

# Docker
docker-compose up  # Start all services
docker-compose down  # Stop all services
```

## Mobile App Development
```bash
# Setup
cd app
bash setup.sh ios     # iOS setup
bash setup.sh android # Android setup

# Development
flutter pub get
flutter run --flavor dev
dart run build_runner build

# Building
flutter build ios --flavor dev --release
flutter build apk --flavor dev --release

# iOS deployment
ios-deploy --bundle build/ios/iphoneos/Runner.app --debug
```

## Firmware Development
```bash
# Using Docker (easiest)
cd omi/firmware
./scripts/build-docker.sh

# Using nRF Connect for VS Code
# Follow official documentation
```

## Documentation
```bash
cd docs
npm install -g mintlify
mintlify dev  # Development server
mintlify broken-links  # Check for broken links
```

## Testing
```bash
# Backend tests
cd backend
python -m pytest

# App tests
cd app
flutter test
flutter drive --target=test_driver/app.dart

# Integration tests
flutter test integration_test/
```

## Git Operations
```bash
git status
git add .
git commit -m "message"
git push origin main
git pull origin main
```