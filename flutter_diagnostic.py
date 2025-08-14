#!/usr/bin/env python3
"""
Flutter Build Diagnostic Script
Helps identify common Flutter build issues after a merge.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def check_flutter_env():
    """Check Flutter environment"""
    print("🔍 Checking Flutter Environment...")
    
    # Check if Flutter is available
    returncode, stdout, stderr = run_command("flutter --version")
    if returncode != 0:
        print("❌ Flutter CLI not found in PATH")
        print("   Run: where flutter")
        return False
    else:
        print("✅ Flutter CLI found")
        print(f"   Version: {stdout.split()[1] if stdout else 'Unknown'}")
    
    # Check Flutter doctor
    returncode, stdout, stderr = run_command("flutter doctor")
    if returncode == 0:
        print("✅ Flutter doctor passed")
    else:
        print("⚠️ Flutter doctor has issues:")
        print(stdout if stdout else stderr)
    
    return True

def check_dart_syntax():
    """Check for Dart syntax errors in key files"""
    print("\n📋 Checking Dart Syntax...")
    
    dart_files = [
        "lib/main.dart",
        "lib/gen/assets.gen.dart",
        "lib/core/app_shell.dart"
    ]
    
    has_errors = False
    for file_path in dart_files:
        if Path(file_path).exists():
            # Try to analyze the Dart file
            returncode, stdout, stderr = run_command(f"dart analyze {file_path}")
            if returncode == 0:
                print(f"✅ {file_path} - No issues")
            else:
                print(f"❌ {file_path} - Has issues:")
                print(stderr if stderr else stdout)
                has_errors = True
        else:
            print(f"⚠️ {file_path} - File not found")
    
    return not has_errors

def check_dependencies():
    """Check pubspec.yaml and dependencies"""
    print("\n📦 Checking Dependencies...")
    
    if not Path("pubspec.yaml").exists():
        print("❌ pubspec.yaml not found")
        return False
    
    # Check for dependency conflicts
    returncode, stdout, stderr = run_command("flutter pub deps")
    if returncode == 0:
        print("✅ Dependencies resolved successfully")
    else:
        print("❌ Dependency resolution failed:")
        print(stderr if stderr else stdout)
        return False
    
    return True

def check_assets():
    """Check for asset issues"""
    print("\n🎨 Checking Assets...")
    
    # Check if assets directory exists and has expected structure
    assets_dir = Path("assets")
    if not assets_dir.exists():
        print("❌ Assets directory not found")
        return False
    
    # Check for generated assets file
    gen_assets = Path("lib/gen/assets.gen.dart")
    if not gen_assets.exists():
        print("❌ Generated assets file missing: lib/gen/assets.gen.dart")
        print("   Run: flutter packages pub run build_runner build")
        return False
    
    # Check if asset images directory exists
    images_dir = assets_dir / "images"
    if images_dir.exists():
        image_count = len(list(images_dir.glob("**/*")))
        print(f"✅ Found {image_count} asset files in images directory")
    
    print("✅ Asset structure looks good")
    return True

def suggest_fixes():
    """Suggest common fixes for Flutter build issues"""
    print("\n🔧 Suggested Fixes:")
    print("1. Clean and rebuild:")
    print("   flutter clean")
    print("   flutter pub get")
    print("   flutter pub run build_runner build --delete-conflicting-outputs")
    print("")
    print("2. Regenerate platform files:")
    print("   cd android && ./gradlew clean && cd ..")
    print("   flutter create . --platforms android,ios")
    print("")
    print("3. Check for conflicting dependencies:")
    print("   flutter pub deps")
    print("   flutter pub outdated")
    print("")
    print("4. Update Flutter and dependencies:")
    print("   flutter upgrade")
    print("   flutter pub upgrade")

def main():
    print("🚀 Flutter Build Diagnostic Tool")
    print("=" * 50)
    
    # Change to app directory if exists
    app_dir = Path("app")
    if app_dir.exists() and app_dir.is_dir():
        os.chdir(app_dir)
        print(f"📂 Working directory: {app_dir.absolute()}")
    else:
        print("📂 Working directory: current")
    
    issues_found = []
    
    # Run diagnostic checks
    if not check_flutter_env():
        issues_found.append("Flutter environment")
    
    if not check_dart_syntax():
        issues_found.append("Dart syntax")
    
    if not check_dependencies():
        issues_found.append("Dependencies")
    
    if not check_assets():
        issues_found.append("Assets")
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 30)
    
    if not issues_found:
        print("✅ No obvious issues found!")
        print("   The build failure might be due to:")
        print("   - Environment-specific configuration")
        print("   - Missing build tools or SDK versions")
        print("   - Platform-specific issues")
    else:
        print("❌ Issues found in:")
        for issue in issues_found:
            print(f"   - {issue}")
        print()
        suggest_fixes()

if __name__ == "__main__":
    main()
