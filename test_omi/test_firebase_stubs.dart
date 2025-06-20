import 'package:flutter/material.dart';
import 'package:omi/utils/firebase/firebase_stubs.dart';

void testFirebaseStubs() {
  print('Testing Firebase stubs...');
  
  // Test Firebase initialization
  try {
    Firebase.initializeApp();
    print('✓ Firebase.initializeApp() works');
  } catch (e) {
    print('✗ Firebase.initializeApp() failed: $e');
  }
  
  // Test FirebaseAuth
  try {
    final auth = FirebaseAuth.instance;
    print('✓ FirebaseAuth.instance works');
    print('  - currentUser: ${auth.currentUser}');
    print('  - authStateChanges: ${auth.authStateChanges()}');
  } catch (e) {
    print('✗ FirebaseAuth failed: $e');
  }
  
  // Test FirebaseMessaging
  try {
    final messaging = FirebaseMessaging.instance;
    print('✓ FirebaseMessaging.instance works');
    print('  - getToken: ${messaging.getToken()}');
  } catch (e) {
    print('✗ FirebaseMessaging failed: $e');
  }
  
  print('Firebase stubs test completed!');
}

void main() {
  testFirebaseStubs();
}
