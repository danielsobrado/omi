# Windows App Testing Guide

This guide provides comprehensive instructions for testing the Omi Windows application, including setup, testing procedures, and troubleshooting.

## Prerequisites

### System Requirements
- Windows 10 (version 1903 or later) or Windows 11
- Visual Studio 2022 with C++ development tools
- Flutter SDK (latest stable version)
- Git for Windows
- Administrator privileges for audio permission testing

### Development Environment Setup
```bash
# Verify Flutter installation
flutter doctor -v

# Check Windows toolchain
flutter doctor --android-licenses
```

## Windows-Specific Components

### Audio Capture System
The Windows app uses platform-specific audio capture through:
- `windows/audio_capture_windows.cpp` - Native audio implementation
- `lib/services/audio_capture_service.dart` - Dart interface
- Windows Audio Session API (WASAPI) integration

### Key Files to Monitor
- `windows/runner/main.cpp` - Application entry point
- `windows/runner/win32_window.cpp` - Window management
- `windows/audio_capture_windows.cpp` - Audio capture implementation
- `windows/CMakeLists.txt` - Build configuration

## Testing Procedures

### 1. Build Testing

#### Debug Build
```bash
# Navigate to app directory
cd /path/to/omi/app

# Clean previous builds
flutter clean

# Get dependencies
flutter pub get

# Build for Windows (debug)
flutter build windows --debug

# Run from build directory
cd build/windows/runner/Debug
./omi.exe
```

#### Release Build
```bash
# Build release version
flutter build windows --release

# Test release build
cd build/windows/runner/Release
./omi.exe
```

#### Profile Build (for performance testing)
```bash
# Build profile version
flutter build windows --profile

# Run with performance monitoring
cd build/windows/runner/Profile
./omi.exe
```

### 2. Audio Functionality Testing

#### Microphone Permission Testing
1. **First Launch Test**
   - Launch the app for the first time
   - Verify microphone permission dialog appears
   - Test both "Allow" and "Deny" scenarios
   - Check app behavior with denied permissions

2. **Audio Input Validation**
   ```bash
   # Test with different audio devices
   # Check Windows Sound settings -> Recording devices
   ```
   - Test with built-in microphone
   - Test with external USB microphone
   - Test with Bluetooth headset
   - Test switching audio devices while app is running

3. **Audio Quality Testing**
   - Record 30-second samples with different devices
   - Check for audio dropouts or distortion
   - Verify audio levels are appropriate
   - Test in noisy and quiet environments

#### Audio Capture Edge Cases
- Test with no microphone connected
- Test microphone hot-plugging (connect/disconnect while app running)
- Test with multiple audio applications running
- Test with system audio muted
- Test with very low/high microphone levels

### 3. Memory Management Testing

#### Memory Leak Detection
```bash
# Run with memory profiling
flutter run --profile --target=lib/main.dart

# Monitor memory usage during:
# - Extended recording sessions (30+ minutes)
# - Multiple start/stop cycles
# - Background/foreground transitions
```

#### Performance Monitoring
- Monitor CPU usage during audio processing
- Check memory consumption over time
- Verify smooth UI performance during recording
- Test battery impact (on laptops)

### 4. UI/UX Testing

#### Window Management
- Test window resizing
- Test minimize/maximize behavior
- Test multiple monitor support
- Verify window restoration after system sleep/wake

#### High DPI Testing
- Test on 4K monitors
- Test with different Windows scaling settings (100%, 125%, 150%, 200%)
- Verify UI elements scale correctly
- Check text readability at all scales

#### Accessibility Testing
- Test with Windows Narrator
- Verify keyboard navigation
- Test high contrast mode
- Check focus indicators

### 5. Integration Testing

#### Backend Connectivity
```bash
# Test API endpoints
# Verify authentication flow
# Test data synchronization
```

#### File System Operations
- Test log file creation and rotation
- Verify temporary file cleanup
- Test with limited disk space
- Check file permissions

### 6. Error Handling Testing

#### Network Issues
- Test with no internet connection
- Test with intermittent connectivity
- Test with slow/high latency connections
- Verify offline mode functionality

#### System Resource Constraints
- Test with low available RAM
- Test with high CPU usage from other apps
- Test with limited disk space
- Test during Windows updates

## Automated Testing

### Unit Tests
```bash
# Run Dart unit tests
flutter test

# Run with coverage
flutter test --coverage
```

### Integration Tests
```bash
# Run integration tests
flutter drive --target=test_driver/app.dart
```

### Windows-Specific Tests
```bash
# Create and run Windows-specific test suite
# Test audio capture functionality
# Test Windows-specific UI behaviors
```

## Common Issues and Solutions

### Audio Issues
1. **No audio input detected**
   - Check Windows privacy settings for microphone access
   - Verify default recording device in Windows Sound settings
   - Check app permissions in Windows Settings > Privacy > Microphone

2. **Poor audio quality**
   - Update audio drivers
   - Check microphone levels in Windows Sound settings
   - Test with different sample rates

3. **Audio dropouts**
   - Check for background apps consuming audio resources
   - Verify adequate system resources (CPU, RAM)
   - Test with different buffer sizes

### Performance Issues
1. **High CPU usage**
   - Check for debug mode vs release mode
   - Monitor background processes
   - Verify audio processing efficiency

2. **Memory leaks**
   - Use Flutter DevTools for memory profiling
   - Check native code for proper resource cleanup
   - Monitor long-running sessions

### Build Issues
1. **CMake errors**
   - Verify Visual Studio C++ tools installation
   - Check Windows SDK version compatibility
   - Update CMake to latest version

2. **Flutter toolchain issues**
   - Run `flutter doctor` and resolve all issues
   - Update Flutter to latest stable version
   - Clear Flutter cache: `flutter clean`

## Test Scenarios Checklist

### Basic Functionality
- [ ] App launches successfully
- [ ] Microphone permission prompt appears
- [ ] Audio recording starts/stops correctly
- [ ] UI responds to user interactions
- [ ] App closes gracefully

### Audio Testing
- [ ] Multiple microphone devices work
- [ ] Audio quality is acceptable
- [ ] No audio dropouts during long sessions
- [ ] Proper handling of audio device changes
- [ ] Background audio recording works

### System Integration
- [ ] Windows notifications work correctly
- [ ] App survives system sleep/wake cycles
- [ ] Multiple monitor support works
- [ ] High DPI scaling works correctly
- [ ] Accessibility features function properly

### Performance Testing
- [ ] Memory usage remains stable over time
- [ ] CPU usage is reasonable
- [ ] UI remains responsive during recording
- [ ] No memory leaks detected
- [ ] Battery usage is acceptable (laptops)

### Error Handling
- [ ] Graceful handling of network failures
- [ ] Proper behavior with no microphone
- [ ] Recovery from audio device errors
- [ ] Appropriate error messages shown
- [ ] App doesn't crash on errors

## Debugging Tools

### Flutter DevTools
```bash
# Launch DevTools
flutter pub global run devtools

# Connect to running app
flutter run --debug
```

### Windows Event Viewer
- Check Application logs for crash reports
- Monitor System logs for driver issues
- Look for audio-related error events

### Process Monitor (ProcMon)
- Monitor file system access
- Track registry access
- Identify resource usage patterns

### Audio Analysis Tools
- Use Windows Sound Recorder for comparison
- Test with Audacity for audio quality verification
- Monitor audio latency with specialized tools

## Reporting Issues

When reporting Windows-specific issues, include:
1. Windows version and build number
2. Audio device information
3. Flutter version and channel
4. Steps to reproduce
5. Expected vs actual behavior
6. Relevant log files
7. System specifications (CPU, RAM, audio drivers)

## Continuous Testing

### Automated CI/CD
- Set up Windows runners for automated testing
- Include audio device simulation in tests
- Monitor performance metrics over time
- Automated regression testing for each release

### User Acceptance Testing
- Beta testing with Windows users
- Feedback collection on audio quality
- Performance testing on various hardware configurations
- Accessibility testing with actual users

---

This guide should be updated as new Windows-specific features are added or issues are discovered during testing.
