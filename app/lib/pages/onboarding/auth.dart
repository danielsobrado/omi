import 'dart:io';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/providers/auth_provider.dart';
import 'package:omi/widgets/consent_bottom_sheet.dart';
import 'package:omi/widgets/username_password_login.dart';
import 'package:provider/provider.dart';

class AuthComponent extends StatefulWidget {
  final VoidCallback onSignIn;

  const AuthComponent({super.key, required this.onSignIn});

  @override
  State<AuthComponent> createState() => _AuthComponentState();
}

class _AuthComponentState extends State<AuthComponent> {
  bool _showUsernamePasswordLogin = false;

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthenticationProvider>(
      builder: (context, provider, child) {
        return Column(
          children: [
            // Background image area - takes remaining space
            Expanded(
              child: Container(), // Just takes up space for background image
            ),

            // Bottom drawer card - wraps content
            Container(
              width: double.infinity,
              padding: EdgeInsets.fromLTRB(32, 26, 32, MediaQuery.of(context).padding.bottom + 8),
              decoration: const BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(40),
                  topRight: Radius.circular(40),
                ),
              ),
              child: SafeArea(
                top: false,
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  transitionBuilder: (Widget child, Animation<double> animation) {
                    return FadeTransition(opacity: animation, child: child);
                  },
                  child: _showUsernamePasswordLogin
                      ? _buildUsernamePasswordLoginContent(provider)
                      : _buildOAuthLoginContent(provider),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildUsernamePasswordLoginContent(AuthenticationProvider provider) {
    return Column(
      key: const ValueKey('username_password'),
      mainAxisSize: MainAxisSize.min,
      children: [
        // Loading indicator or spacing
        SizedBox(
          height: 20,
          child: provider.loading
              ? const Center(
                  child: CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation(Colors.white),
                  ),
                )
              : null,
        ),

        // Title text
        const Text(
          'Sign In to Continue',
          style: TextStyle(
            color: Colors.white,
            fontSize: 28,
            fontWeight: FontWeight.bold,
            height: 1.2,
            fontFamily: 'Manrope',
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 32),

        // Username/Password login form
        UsernamePasswordLogin(
          onSignIn: widget.onSignIn,
          isDarkMode: true,
        ),

        const SizedBox(height: 24),

        // Switch to OAuth button
        TextButton.icon(
          onPressed: provider.loading ? null : () {
            setState(() {
              _showUsernamePasswordLogin = false;
            });
          },
          icon: const Icon(
            Icons.arrow_back,
            color: Colors.white,
            size: 16,
          ),
          label: const Text(
            'Back to OAuth Login',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w500,
              fontFamily: 'Manrope',
            ),
          ),
        ),

        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildOAuthLoginContent(AuthenticationProvider provider) {
    return Column(
      key: const ValueKey('oauth'),
      mainAxisSize: MainAxisSize.min,
      children: [
        // Loading indicator or spacing
        SizedBox(
          height: 20,
          child: provider.loading
              ? const Center(
                  child: CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation(Colors.white),
                  ),
                )
              : null,
        ),

        // Title text
        const Text(
          'Speak. Transcribe. Summarize.',
          style: TextStyle(
            color: Colors.white,
            fontSize: 32,
            fontWeight: FontWeight.bold,
            height: 1.2,
            fontFamily: 'Manrope',
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 32),

        // Sign in buttons
        if (Platform.isIOS || Platform.isMacOS) ...[
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: () {
                HapticFeedback.mediumImpact();
                ConsentBottomSheet.show(
                  context,
                  authMethod: 'apple',
                  onContinue: () async {
                    final user = FirebaseAuth.instance.currentUser;
                    if (user != null && user.isAnonymous && SharedPreferencesUtil().hasPersonaCreated) {
                      await provider.linkWithApple();
                      if (mounted) {
                        SharedPreferencesUtil().hasOmiDevice = true;
                        SharedPreferencesUtil().verifiedPersonaId = null;
                        widget.onSignIn();
                      }
                    } else {
                      provider.onAppleSignIn(widget.onSignIn);
                    }
                  },
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(28),
                ),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(FontAwesomeIcons.apple, size: 24),
                  SizedBox(width: 8),
                  Text(
                    'Sign in with Apple',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      fontFamily: 'Manrope',
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],

        // Google sign in button
        SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: () {
              HapticFeedback.mediumImpact();
              ConsentBottomSheet.show(
                context,
                authMethod: 'google',
                onContinue: () async {
                  final user = FirebaseAuth.instance.currentUser;
                  if (user != null && user.isAnonymous && SharedPreferencesUtil().hasPersonaCreated) {
                    await provider.linkWithGoogle();
                    if (mounted) {
                      SharedPreferencesUtil().hasOmiDevice = true;
                      SharedPreferencesUtil().verifiedPersonaId = null;
                      widget.onSignIn();
                    }
                  } else {
                    provider.onGoogleSignIn(widget.onSignIn);
                  }
                },
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Colors.black,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(28),
              ),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(FontAwesomeIcons.google, size: 20),
                SizedBox(width: 8),
                Text(
                  'Sign in with Google',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    fontFamily: 'Manrope',
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),

        // Divider with "OR"
        Row(
          children: [
            Expanded(
              child: Container(
                height: 1,
                color: Colors.white.withValues(alpha: 0.3),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'OR',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.6),
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  fontFamily: 'Manrope',
                ),
              ),
            ),
            Expanded(
              child: Container(
                height: 1,
                color: Colors.white.withValues(alpha: 0.3),
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),

        // Username/Password login button
        SizedBox(
          width: double.infinity,
          height: 56,
          child: OutlinedButton(
            onPressed: provider.loading ? null : () {
              setState(() {
                _showUsernamePasswordLogin = true;
              });
            },
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              side: const BorderSide(color: Colors.white, width: 1.5),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(28),
              ),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.person, size: 20),
                SizedBox(width: 8),
                Text(
                  'Sign in with Username',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    fontFamily: 'Manrope',
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 24),

        // Privacy policy text
        RichText(
          textAlign: TextAlign.center,
          text: TextSpan(
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.6),
              fontSize: 11,
              fontFamily: 'Manrope',
            ),
            children: [
              const TextSpan(text: 'By continuing, you agree to our '),
              TextSpan(
                text: 'Privacy Policy',
                style: const TextStyle(
                  decoration: TextDecoration.underline,
                ),
                recognizer: TapGestureRecognizer()..onTap = provider.openPrivacyPolicy,
              ),
              const TextSpan(text: ' & '),
              TextSpan(
                text: 'Terms of Use',
                style: const TextStyle(
                  decoration: TextDecoration.underline,
                ),
                recognizer: TapGestureRecognizer()..onTap = provider.openTermsOfService,
              ),
              const TextSpan(text: '.'),
            ],
          ),
        ),

        const SizedBox(height: 16),
      ],
    );
  }
}
