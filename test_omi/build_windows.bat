#!/bin/bash
cd "C:\Dev\omi\test_omi"
echo "Cleaning Flutter project..."
flutter clean
echo "Getting dependencies..."
flutter pub get
echo "Building for Windows..."
flutter build windows --debug
