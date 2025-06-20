// Firebase stubs for Windows platform

class Firebase {
  static Future<void> initializeApp({dynamic options}) async {
    print('Mock Firebase initialized for Windows');
  }
}

class FirebaseAuth {
  static FirebaseAuth? _instance;
  static FirebaseAuth get instance => _instance ??= FirebaseAuth._();
  FirebaseAuth._();

  User? get currentUser => null;
  
  Future<UserCredential> signInWithCredential(dynamic credential) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<UserCredential> signInWithPopup(dynamic provider) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<UserCredential> createUserWithEmailAndPassword({
    required String email,
    required String password,
  }) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<void> signOut() async {
    // Mock implementation
  }
  
  Future<void> sendPasswordResetEmail({required String email}) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Stream<User?> authStateChanges() {
    return Stream<User?>.value(null);
  }
  
  Stream<User?> userChanges() {
    return Stream<User?>.value(null);
  }
  
  Future<void> deleteUser() async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
}

class User {
  String? get email => null;
  String? get uid => null;
  String? get displayName => null;
  String? get photoURL => null;
  bool get emailVerified => false;
  
  Future<void> updateDisplayName(String? displayName) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<void> updatePhotoURL(String? photoURL) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<void> delete() async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<IdTokenResult> getIdTokenResult([bool forceRefresh = false]) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
  
  Future<String> getIdToken([bool forceRefresh = false]) async {
    throw UnimplementedError('Firebase not supported on Windows');
  }
}

class UserCredential {
  User? get user => null;
  AuthCredential? get credential => null;
}

class AuthCredential {}

class IdTokenResult {
  String? get token => null;
  Map<String, dynamic>? get claims => null;
}

class FirebaseAuthException implements Exception {
  final String code;
  final String? message;
  
  FirebaseAuthException({required this.code, this.message});
  
  @override
  String toString() => 'FirebaseAuthException: $code${message != null ? ' - $message' : ''}';
}

class GoogleAuthProvider {
  static AuthCredential credential({String? accessToken, String? idToken}) {
    throw UnimplementedError('Firebase not supported on Windows');
  }
}

class OAuthProvider {
  OAuthProvider(String providerId);
  
  OAuthProvider addScope(String scope) => this;
  OAuthProvider setCustomParameters(Map<String, String> parameters) => this;
}

class AppleAuthProvider {
  static AuthCredential credential({
    required String idToken,
    String? accessToken,
  }) {
    throw UnimplementedError('Firebase not supported on Windows');
  }
}

// Firebase Messaging stubs
class FirebaseMessaging {
  static FirebaseMessaging? _instance;
  static FirebaseMessaging get instance => _instance ??= FirebaseMessaging._();
  FirebaseMessaging._();
  
  Future<String?> getToken() async => null;
  
  Future<void> requestPermission() async {}
  
  Stream<RemoteMessage> get onMessage => Stream<RemoteMessage>.empty();
  Stream<RemoteMessage> get onMessageOpenedApp => Stream<RemoteMessage>.empty();
  
  static Future<RemoteMessage?> getInitialMessage() async => null;
  
  Future<void> subscribeToTopic(String topic) async {}
  Future<void> unsubscribeFromTopic(String topic) async {}
}

class RemoteMessage {
  RemoteNotification? get notification => null;
  Map<String, dynamic> get data => {};
  String? get messageId => null;
  String? get from => null;
}

class RemoteNotification {
  String? get title => null;
  String? get body => null;
  String? get android => null;
  String? get apple => null;
}
