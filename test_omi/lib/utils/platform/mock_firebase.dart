// Mock Firebase implementation for Windows
class MockFirebase {
  static Future<void> initializeApp({dynamic options}) async {
    // Mock implementation - do nothing
    print('Mock Firebase initialized for Windows');
  }
}

class MockFirebaseAuth {
  static MockFirebaseAuth? _instance;
  static MockFirebaseAuth get instance => _instance ??= MockFirebaseAuth._();
  MockFirebaseAuth._();

  MockUser? get currentUser => null;
  
  Future<void> signOut() async {
    // Mock implementation
  }
}

class MockUser {
  String? get email => null;
  String? get uid => null;
}
