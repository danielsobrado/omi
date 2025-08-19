# App Configuration

This file contains feature flags and configuration options for the OMI app.

## Authentication Configuration

### useGoogleAuth (boolean)
- **Default**: 	rue
- **Description**: Controls the primary authentication method
- Set to 	rue to use Google/Apple authentication (recommended)
- Set to alse to use username/password authentication with demo credentials

### showUsernamePasswordFallback (boolean)
- **Default**: 	rue
- **Description**: When Google auth is enabled, shows a fallback option for username/password
- Only applies when useGoogleAuth is 	rue

### Demo Credentials
- **Username**: dmin
- **Password**: dmin
- Used when useGoogleAuth is set to alse

## Quick Setup Examples

### For Production (Google Auth):
`dart
static const bool useGoogleAuth = true;
static const bool showUsernamePasswordFallback = false;
`

### For Demo/Testing (Username/Password):
`dart
static const bool useGoogleAuth = false;
static const bool showUsernamePasswordFallback = true;
`

### For Development (Both options available):
`dart
static const bool useGoogleAuth = true;
static const bool showUsernamePasswordFallback = true;
`

## Notes
- Changes require app restart to take effect
- Make sure Firebase/Google auth is properly configured when using Google auth
- Demo credentials are hardcoded and should only be used for testing
