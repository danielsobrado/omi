import 'dart:io';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:omi/config/app_config.dart';
import 'package:omi/providers/auth_provider.dart';
import 'package:omi/widgets/username_password_login.dart';
import 'package:provider/provider.dart';

class AuthComponent extends StatefulWidget {
  final VoidCallback onSignIn;

  const AuthComponent({super.key, required this.onSignIn});

  @override
  State<AuthComponent> createState() => _AuthComponentState();
}

class _AuthComponentState extends State<AuthComponent> {
  bool _showUsernamePassword = false;

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
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.7), // 30% transparency
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(40),
                  topRight: Radius.circular(40),
                ),
              ),
              child: SafeArea(
                top: false,
                child: Column(
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

                    // Authentication content based on configuration
                    _buildAuthContent(context, provider),

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
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildAuthContent(BuildContext context, AuthenticationProvider provider) {
    // If Google auth is disabled, show only username/password
    if (!AppConfig.useGoogleAuth) {
      return UsernamePasswordLogin(
        onSignIn: widget.onSignIn,
        isDarkMode: true,
      );
    }

    // If showing username/password fallback
    if (_showUsernamePassword) {
      return Column(
        children: [
          UsernamePasswordLogin(
            onSignIn: widget.onSignIn,
            isDarkMode: true,
          ),
          if (AppConfig.showUsernamePasswordFallback) ...[
            const SizedBox(height: 16),
            TextButton(
              onPressed: () {
                setState(() {
                  _showUsernamePassword = false;
                });
              },
              child: const Text(
                'Back to Google Sign In',
                style: TextStyle(
                  color: Colors.white70,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          ],
        ],
      );
    }

    // Default: Show Google auth
    return Column(
      children: [
        // Google Sign In Button
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton.icon(
            onPressed: provider.loading
                ? null
                : () async {
                    HapticFeedback.mediumImpact();
                    await provider.onGoogleSignIn(widget.onSignIn);
                  },
            icon: const FaIcon(
              FontAwesomeIcons.google,
              color: Colors.black,
              size: 18,
            ),
            label: const Text(
              'Continue with Google',
              style: TextStyle(
                color: Colors.black,
                fontSize: 16,
                fontWeight: FontWeight.w600,
                fontFamily: 'Manrope',
              ),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Colors.black,
              elevation: 2,
              shadowColor: Colors.black.withValues(alpha: 0.2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(25),
              ),
            ),
          ),
        ),

        // Apple Sign In Button (iOS only)
        if (Platform.isIOS) ...[
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              onPressed: provider.loading
                  ? null
                  : () async {
                      HapticFeedback.mediumImpact();
                      await provider.onAppleSignIn(widget.onSignIn);
                    },
              icon: const FaIcon(
                FontAwesomeIcons.apple,
                color: Colors.white,
                size: 18,
              ),
              label: const Text(
                'Continue with Apple',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  fontFamily: 'Manrope',
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
                elevation: 2,
                shadowColor: Colors.black.withValues(alpha: 0.2),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                  side: const BorderSide(color: Colors.white24),
                ),
              ),
            ),
          ),
        ],

        // Username/Password fallback option
        if (AppConfig.showUsernamePasswordFallback) ...[
          const SizedBox(height: 20),
          const Row(
            children: [
              Expanded(child: Divider(color: Colors.white24)),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  'or',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                    fontFamily: 'Manrope',
                  ),
                ),
              ),
              Expanded(child: Divider(color: Colors.white24)),
            ],
          ),
          const SizedBox(height: 20),
          TextButton(
            onPressed: () {
              setState(() {
                _showUsernamePassword = true;
              });
            },
            child: const Text(
              'Use Username & Password',
              style: TextStyle(
                color: Colors.white70,
                decoration: TextDecoration.underline,
                fontSize: 14,
                fontFamily: 'Manrope',
              ),
            ),
          ),
        ],

        // Debug info (if enabled)
        if (AppConfig.showDebugInfo) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white10,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Auth Mode: ',
              style: const TextStyle(
                color: Colors.white54,
                fontSize: 10,
                fontFamily: 'monospace',
              ),
            ),
          ),
        ],
      ],
    );
  }
}
