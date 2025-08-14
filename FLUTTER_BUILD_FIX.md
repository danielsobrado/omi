# Flutter Build Fix Guide

## 🚨 Quick Fix for Post-Merge Build Failure

The Flutter build is failing after our major merge. Here are the most likely fixes:

### 1. Clean and Regenerate Everything
```bash
cd app

# Clean all build artifacts
flutter clean
rm -rf build/
rm -rf .dart_tool/
rm -rf android/build/
rm -rf android/app/build/

# Regenerate dependencies
flutter pub get

# Regenerate assets
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### 2. Fix Asset Generation Issues
The `assets.gen.dart` file may be out of sync with actual assets:

```bash
cd app

# Force regenerate assets
flutter packages pub run build_runner clean
flutter packages pub run build_runner build --delete-conflicting-outputs

# Or use flutter_gen directly
flutter packages pub run flutter_gen_runner
```

### 3. Check for Missing Dependencies
```bash
cd app

# Check dependency status
flutter pub deps
flutter pub outdated

# Update if needed
flutter pub upgrade
```

### 4. Android-Specific Fixes
```bash
cd app

# Clean Android builds
cd android
./gradlew clean
cd ..

# Regenerate Android platform files
flutter create . --platforms android

# Try building Android specifically
flutter build apk --debug --flavor dev
```

### 5. If All Else Fails - Nuclear Option
```bash
cd app

# Complete reset
flutter clean
rm -rf build/ .dart_tool/ android/build/ android/app/build/
rm pubspec.lock

# Regenerate everything
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
flutter create . --platforms android,ios

# Try build again
flutter build apk --debug --flavor dev
```

## 🔍 Specific Issues from Our Merge

### Missing Assets
The merge added new assets like:
- `apple-reminders-logo.png`
- Various onboarding images
- New device images

If assets are missing, regenerate them:
```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### Dependency Conflicts
The merge may have introduced dependency conflicts. Check:
```bash
flutter pub deps
```

### Android Build Issues
The Android build configuration was updated. If you get signing errors:
1. Make sure `key.properties` exists
2. Check Android SDK versions
3. Verify NDK version matches requirements

### Environment Variables
Make sure these are set if testing locally:
- `INTERCOM_APP_ID`
- `INTERCOM_ANDROID_API_KEY`

## 📋 Step-by-Step Troubleshooting

1. **Start with asset regeneration** (most likely fix)
2. **Clean build if assets don't help**
3. **Check dependencies for conflicts**
4. **Try Android-specific fixes**
5. **Use nuclear option as last resort**

## 🎯 Most Likely Solution

Based on the merge we just completed, the issue is probably **asset generation**. Run this:

```bash
cd app
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
flutter build apk --debug --flavor dev
```

This should resolve the build issue in 90% of cases after a major merge.
