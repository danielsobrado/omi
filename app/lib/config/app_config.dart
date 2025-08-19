class AppConfig {
  // Authentication Configuration
  static const bool useGoogleAuth = true; // Set to false to use username/password
  static const bool showUsernamePasswordFallback = true; // Show fallback option when Google auth is enabled
  
  // Demo credentials (used when useGoogleAuth is false)
  static const String demoUsername = 'admin';
  static const String demoPassword = 'admin';
  
  // UI Configuration
  static const bool showDebugInfo = false;
  
  // Feature Flags
  static const bool enableBiometricAuth = false;
  static const bool enableOfflineMode = false;
}
