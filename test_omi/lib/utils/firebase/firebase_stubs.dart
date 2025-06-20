/// Firebase stub implementations for platforms without Firebase support
/// Provides non-functional placeholders to enable compilation
/// Includes mock user for testing

class User {
  String get uid => 'mock-uid';
  String? get email => null;
  String? get displayName => null;
  String? get photoURL => null;
  bool get isAnonymous => true;
  
  Future<void> updateProfile({String? displayName, String? photoURL}) async {}
  Future<void> reload() async {}
  Future<UserCredential> linkWithCredential(AuthCredential credential) async => throw UnsupportedError('Firebase not available');
  Future<UserCredential> linkWithProvider(AuthProvider provider) async => throw UnsupportedError('Firebase not available');
  Future<IdTokenResult> getIdTokenResult([bool forceRefresh = false]) async => IdTokenResult._();
  Future<void> delete() async {}
}

class _MockUser extends User {
  static _MockUser? _instance;
  
  @override
  String get uid => 'mock-user-123';
  @override
  String? get email => 'test@example.com';
  @override
  String? get displayName => 'Test User';
  @override
  String? get photoURL => null;
  @override
  bool get isAnonymous => false;
}

class FirebaseAuth {
  static FirebaseAuth get instance => FirebaseAuth._();
  FirebaseAuth._();
  
  static _MockUser? _currentUser;
  static bool _isSignedIn = false;
  
  User? get currentUser => _isSignedIn ? (_MockUser._instance ??= _MockUser()) : null;
  
  Stream<User?> authStateChanges() {
    return Stream.value(_isSignedIn ? (_MockUser._instance ??= _MockUser()) : null);
  }
  
  Stream<User?> idTokenChanges() {
    return Stream.value(_isSignedIn ? (_MockUser._instance ??= _MockUser()) : null);
  }
  
  Future<UserCredential> signInAnonymously() async {
    _isSignedIn = true;
    _MockUser._instance = _MockUser();
    print('Mock Firebase: Signed in anonymously');
    return UserCredential._mock();
  }
  
  Future<UserCredential> signInWithCredential(AuthCredential credential) async {
    _isSignedIn = true;
    _MockUser._instance = _MockUser();
    print('Mock Firebase: Signed in with credential');
    return UserCredential._mock();
  }
  
  Future<UserCredential> signInWithProvider(AuthProvider provider) async {
    _isSignedIn = true;
    _MockUser._instance = _MockUser();
    print('Mock Firebase: Signed in with provider');
    return UserCredential._mock();
  }
  
  Future<void> signOut() async {
    _isSignedIn = false;
    _MockUser._instance = null;
    print('Mock Firebase: Signed out');
  }
}

class UserCredential {
  UserCredential._mock();
  
  User? get user => FirebaseAuth.instance.currentUser;
  AdditionalUserInfo? get additionalUserInfo => AdditionalUserInfo._mock();
  AuthCredential? get credential => null;
}

class AdditionalUserInfo {
  AdditionalUserInfo._mock();
  
  bool get isNewUser => false;
  String? get username => 'testuser';
  Map<String, dynamic>? get profile => {
    'given_name': 'Test',
    'family_name': 'User',
    'email': 'test@example.com',
  };
}

class IdTokenResult {
  IdTokenResult._();
  String get token => 'mock-token';
  DateTime? get expirationTime => null;
}

class AuthCredential {
  String get providerId => 'mock-provider';
  String get signInMethod => 'mock-signin-method';
  String? get accessToken => null;
  String? get idToken => null;
}

class AuthProvider {}

class OAuthProvider extends AuthProvider {
  OAuthProvider(String providerId);
  
  static AuthCredential credential({String? idToken, String? accessToken, String? rawNonce}) {
    return AuthCredential();
  }
}

class GoogleAuthProvider {
  static AuthCredential credential({String? idToken, String? accessToken}) => AuthCredential();
}

class AppleAuthProvider extends AuthProvider {
  AppleAuthProvider();
  static AuthCredential credential({String? idToken, String? accessToken}) => AuthCredential();
}

class FacebookAuthProvider {
  static AuthCredential credential(String accessToken) => AuthCredential();
}

class FirebaseAuthException implements Exception {
  final String code;
  final String? message;
  AuthCredential? get credential => null;
  
  FirebaseAuthException({required this.code, this.message});
  
  @override
  String toString() => 'FirebaseAuthException: [$code] $message';
}

class FirebaseMessaging {
  static FirebaseMessaging get instance => FirebaseMessaging._();
  FirebaseMessaging._();
  
  Future<String?> getToken() async => null;
  Future<String?> getAPNSToken() async => null;
  Stream<String> get onTokenRefresh => Stream.empty();
  static Stream<RemoteMessage> get onMessage => Stream.empty();
  Stream<RemoteMessage> get onMessageOpenedApp => Stream.empty();
  
  Future<void> requestPermission([MessagingSettings? settings]) async {}
  Future<void> subscribeToTopic(String topic) async {}
  Future<void> unsubscribeFromTopic(String topic) async {}
  Future<RemoteMessage?> getInitialMessage() async => null;
}

class MessagingSettings {
  final bool alert;
  final bool announcement;
  final bool badge;
  final bool carPlay;
  final bool criticalAlert;
  final bool provisional;
  final bool sound;
  
  const MessagingSettings({
    this.alert = true,
    this.announcement = false,
    this.badge = true,
    this.carPlay = false,
    this.criticalAlert = false,
    this.provisional = false,
    this.sound = true,
  });
}

class RemoteMessage {
  String? get messageId => null;
  Map<String, dynamic> get data => {};
  RemoteNotification? get notification => null;
  String? get from => null;
  DateTime? get sentTime => null;
}

class RemoteNotification {
  String? get title => null;
  String? get body => null;
  String? get android => null;
  String? get apple => null;
}

class FirebaseCore {
  static Future<void> ensureInitialized() async {}
}

class Firebase {
  static Future<void> initializeApp() async {}
}
