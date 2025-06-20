# Firebase Mock Implementation for Windows

## Overview
This project has been modified to work on Windows by replacing Firebase dependencies with mock implementations.

## What was changed:

### 1. Firebase Dependencies Removed
- All Firebase packages are commented out in `pubspec.yaml`
- `firebase_core`, `firebase_auth`, and `firebase_messaging` are no longer dependencies

### 2. Firebase Stubs Created
- Created `lib/utils/firebase/firebase_stubs.dart` with mock implementations
- All Firebase classes return dummy data or throw `UnsupportedError` for Windows

### 3. Import Updates
- All Firebase imports now point to `package:omi/utils/firebase/firebase_stubs.dart`
- Updated files:
  - `lib/main.dart`
  - `lib/backend/auth.dart`
  - `lib/providers/auth_provider.dart`
  - `lib/services/notifications/notification_service_fcm.dart`
  - `lib/pages/onboarding/wrapper.dart`
  - `lib/pages/onboarding/auth.dart`
  - `lib/pages/settings/change_name_widget.dart`
  - `lib/pages/settings/delete_account.dart`
  - `lib/pages/persona/twitter/social_profile.dart`
  - `lib/pages/persona/twitter/clone_success_sceen.dart`

## Building for Windows

1. Clean the project:
   ```bash
   flutter clean
   ```

2. Get dependencies:
   ```bash
   flutter pub get
   ```

3. Generate any missing files:
   ```bash
   dart run build_runner build --delete-conflicting-outputs
   ```

4. Build for Windows:
   ```bash
   flutter build windows --debug
   ```

## How Firebase Stubs Work

- **Authentication**: All auth methods return null users or throw UnsupportedError
- **Messaging**: All messaging methods return null tokens or empty streams
- **Core**: Initialization is a no-op (returns immediately)

The app will compile and run but Firebase features will be non-functional. This allows the Windows build to complete successfully while maintaining the same code structure for other platforms.

## Re-enabling Firebase for Other Platforms

To restore Firebase functionality for iOS/Android/Web:

1. Uncomment Firebase dependencies in `pubspec.yaml`
2. Replace stub imports with conditional imports:
   ```dart
   import 'package:firebase_auth/firebase_auth.dart' if (dart.library.io) 'package:omi/utils/firebase/firebase_stubs.dart';
   ```
3. Restore platform-specific initialization in `main.dart`

## Known Limitations

- Firebase authentication will not work (users will appear as signed out)
- Push notifications will not work
- Any Firebase-dependent features will fail gracefully
- App will run but with limited functionality compared to mobile platforms
