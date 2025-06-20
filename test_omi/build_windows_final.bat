#!/bin/bash
echo "Building Flutter Windows with Firebase Stubs..."
cd "C:\Dev\omi\test_omi"
flutter clean
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter build windows --debug
echo "Build process completed!"
