import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:omi/providers/auth_provider.dart';

class UsernamePasswordLogin extends StatefulWidget {
  final VoidCallback onSignIn;
  final bool isDarkMode;

  const UsernamePasswordLogin({
    super.key,
    required this.onSignIn,
    this.isDarkMode = true,
  });

  @override
  State<UsernamePasswordLogin> createState() => _UsernamePasswordLoginState();
}

class _UsernamePasswordLoginState extends State<UsernamePasswordLogin> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController(text: 'admin');
  final _passwordController = TextEditingController(text: 'admin');
  bool _isPasswordVisible = false;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleSubmit() {
    if (_formKey.currentState!.validate()) {
      final provider = context.read<AuthenticationProvider>();
      provider.onEmailPasswordSignIn(
        _usernameController.text.trim(),
        _passwordController.text.trim(),
        widget.onSignIn,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final textColor = widget.isDarkMode ? Colors.white : Colors.black;
    final hintColor = widget.isDarkMode ? Colors.white.withValues(alpha: 0.6) : Colors.black.withValues(alpha: 0.6);

    return Consumer<AuthenticationProvider>(
      builder: (context, provider, child) {
        return Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Login with Username & Password',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: textColor,
                  fontFamily: 'Manrope',
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 20),
              
              // Username field
              TextFormField(
                controller: _usernameController,
                enabled: !provider.loading,
                style: TextStyle(color: textColor),
                decoration: InputDecoration(
                  labelText: 'Username',
                  hintText: 'Enter username (admin)',
                  hintStyle: TextStyle(color: hintColor),
                  labelStyle: TextStyle(color: hintColor),
                  prefixIcon: Icon(Icons.person_outline, color: hintColor),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: hintColor, width: 1),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.blue, width: 2),
                  ),
                  errorBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.red, width: 1),
                  ),
                  focusedErrorBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.red, width: 2),
                  ),
                  filled: true,
                  fillColor: widget.isDarkMode 
                    ? Colors.white.withValues(alpha: 0.1) 
                    : Colors.grey.withValues(alpha: 0.1),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Username is required';
                  }
                  return null;
                },
              ),
              
              const SizedBox(height: 16),
              
              // Password field
              TextFormField(
                controller: _passwordController,
                enabled: !provider.loading,
                obscureText: !_isPasswordVisible,
                style: TextStyle(color: textColor),
                decoration: InputDecoration(
                  labelText: 'Password',
                  hintText: 'Enter password (admin)',
                  hintStyle: TextStyle(color: hintColor),
                  labelStyle: TextStyle(color: hintColor),
                  prefixIcon: Icon(Icons.lock_outline, color: hintColor),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _isPasswordVisible ? Icons.visibility_off : Icons.visibility,
                      color: hintColor,
                    ),
                    onPressed: () {
                      setState(() {
                        _isPasswordVisible = !_isPasswordVisible;
                      });
                    },
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: hintColor, width: 1),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.blue, width: 2),
                  ),
                  errorBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.red, width: 1),
                  ),
                  focusedErrorBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Colors.red, width: 2),
                  ),
                  filled: true,
                  fillColor: widget.isDarkMode 
                    ? Colors.white.withValues(alpha: 0.1) 
                    : Colors.grey.withValues(alpha: 0.1),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Password is required';
                  }
                  return null;
                },
              ),
              
              const SizedBox(height: 24),
              
              // Sign in button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: provider.loading ? null : _handleSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(28),
                    ),
                    elevation: provider.loading ? 0 : 2,
                  ),
                  child: provider.loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.login, size: 20),
                            SizedBox(width: 8),
                            Text(
                              'Sign In',
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
              
              const SizedBox(height: 12),
              
              // Demo credentials hint
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: widget.isDarkMode 
                    ? Colors.blue.withValues(alpha: 0.1) 
                    : Colors.blue.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: Colors.blue.withValues(alpha: 0.3),
                    width: 1,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.info_outline,
                      color: Colors.blue,
                      size: 16,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Demo credentials: admin / admin',
                        style: TextStyle(
                          color: Colors.blue,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
