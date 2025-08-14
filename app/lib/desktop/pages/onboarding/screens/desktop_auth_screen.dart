import 'package:flutter/material.dart';
import 'package:omi/utils/responsive/responsive_helper.dart';
import 'package:omi/gen/assets.gen.dart';
import 'package:omi/widgets/username_password_login.dart';

class DesktopAuthScreen extends StatefulWidget {
  final VoidCallback onSignIn;

  const DesktopAuthScreen({super.key, required this.onSignIn});

  @override
  State<DesktopAuthScreen> createState() => _DesktopAuthScreenState();
}

class _DesktopAuthScreenState extends State<DesktopAuthScreen> {
  @override
  Widget build(BuildContext context) {
    final responsive = ResponsiveHelper(context);

    return Scaffold(
      backgroundColor: ResponsiveHelper.backgroundPrimary,
      body: Container(
        decoration: BoxDecoration(
          gradient: responsive.backgroundGradient,
        ),
        child: SafeArea(
          child: Center(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 480),
              padding: responsive.contentPadding(basePadding: 40),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      color: ResponsiveHelper.backgroundSecondary,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Assets.images.logoTransparent.image(
                      width: 88,
                      height: 88,
                    ),
                  ),

                  SizedBox(height: responsive.spacing(baseSpacing: 32)),

                  Text(
                    'Sign In to Continue',
                    style: responsive.headlineLarge.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                    textAlign: TextAlign.center,
                  ),

                  SizedBox(height: responsive.spacing(baseSpacing: 12)),

                  Text(
                    'Enter your credentials to access your account.',
                    style: responsive.bodyLarge.copyWith(
                      color: ResponsiveHelper.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),

                  SizedBox(height: responsive.spacing(baseSpacing: 48)),

                  // Username/Password login form
                  UsernamePasswordLogin(
                    onSignIn: widget.onSignIn,
                    isDarkMode: false,
                  ),

                  SizedBox(height: responsive.spacing(baseSpacing: 32)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
