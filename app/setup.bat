@ECHO OFF
SETLOCAL

:: This is a Windows Batch file equivalent of the original bash script.
::
:: Set up the Omi Mobile Project(iOS/Android).
::
:: Prerequisites (stable versions, use these or higher):
::
:: Common for all developers:
:: - Flutter SDK (v3.32.4)
:: - Opus Codec: https://opus-codec.org
::
:: For iOS Developers (REQUIRES A MACOS MACHINE):
:: - Xcode (v16.4)
:: - CocoaPods (v1.16.2)
::
:: For Android Developers:
:: - Android Studio (Iguana | 2024.3)
:: - Android SDK Platform (API 35)
:: - JDK (v21)
:: - Gradle (v8.10)
:: - NDK (27.0.12077973)
:: Usages:
:: - > setup.bat ios
:: - > setup.bat android

ECHO [INFO] Welcome to the OMI Mobile Project - We're hiring! Join us on Discord: http://discord.omi.me
ECHO Prerequisites (stable versions, use these or higher):
ECHO.
ECHO Common for all developers:
ECHO - Flutter SDK (v3.32.4)
ECHO - Opus Codec: https://opus-codec.org
ECHO.
ECHO For iOS Developers (REQUIRES A MACOS MACHINE):
ECHO - Xcode (v16.4)
ECHO - CocoaPods (v1.16.2)
ECHO.
ECHO For Android Developers:
ECHO - Android Studio (Iguana ^| 2024.3)
ECHO - Android SDK Platform (API 35)
ECHO - JDK (v21)
ECHO - Gradle (v8.10)
ECHO - NDK (27.0.12077973)
ECHO.
ECHO Usages:
ECHO - setup.bat ios
ECHO - setup.bat android
ECHO.

SET "API_BASE_URL=https://backend-dt5lrfkkoa-uc.a.run.app/"

:: ##################################################################
:: Main logic block - determines which platform setup to run
:: ##################################################################

IF /I "%1" == "ios" (
    CALL :setup_ios
) ELSE IF /I "%1" == "android" (
    CALL :setup_android
) ELSE (
    CALL :error "Unexpected platform '%1'. Please use 'ios' or 'android'."
)

GOTO :EOF

:: ##################################################################
:: Subroutines (equivalent to Bash functions)
:: ##################################################################

:setup_ios
    ECHO.
    ECHO ### Running iOS Setup ###
    ECHO.

    CALL :setup_firebase
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :setup_app_env
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :setup_provisioning_profile
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :build_ios
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    ECHO.
    ECHO [SUCCESS] iOS setup completed successfully.
GOTO :EOF

:setup_android
    ECHO.
    ECHO ### Running Android Setup ###
    ECHO.

    CALL :setup_keystore_android
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :setup_firebase
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :setup_app_env
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    CALL :build
    IF %ERRORLEVEL% NEQ 0 GOTO :handle_error

    ECHO.
    ECHO [SUCCESS] Android setup completed successfully.
GOTO :EOF


:setup_firebase
    ECHO --- Setting up Firebase with prebuilt configs...
    mkdir android\app\src\dev\ 2>NUL
    mkdir ios\Config\Dev\ 2>NUL
    mkdir ios\Runner\ 2>NUL
    copy setup\prebuilt\firebase_options.dart lib\firebase_options_dev.dart
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1
    copy setup\prebuilt\google-services.json android\app\src\dev\
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1
    copy setup\prebuilt\GoogleService-Info.plist ios\Config\Dev\
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1
    copy setup\prebuilt\GoogleService-Info.plist ios\Runner\
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1

    :: Warn: Mocking, should remove
    mkdir android\app\src\prod\ 2>NUL
    mkdir ios\Config\Prod\ 2>NUL
    copy setup\prebuilt\firebase_options.dart lib\firebase_options_prod.dart
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1
    copy setup\prebuilt\google-services.json android\app\src\prod\
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1
    copy setup\prebuilt\GoogleService-Info.plist ios\Config\Prod\
GOTO :EOF

:setup_provisioning_profile
    ECHO.
    ECHO [WARNING] iOS Provisioning Profile setup requires a macOS environment.
    ECHO [WARNING] This step uses 'fastlane', which is typically installed via 'brew' on a Mac.
    ECHO [WARNING] This section WILL fail on a standard Windows machine.
    ECHO.
    ECHO --- Attempting to set up provisioning profile...

    where fastlane >nul 2>nul
    IF %ERRORLEVEL% NEQ 0 (
        ECHO 'fastlane' command not found. This step cannot continue on Windows.
        EXIT /B 1
    )
    SET "MATCH_PASSWORD=omi"
    fastlane match development --readonly ^
        --app_identifier com.friend-app-with-wearable.ios12.development ^
        --git_url "git@github.com:BasedHardware/omi-community-certs.git"
GOTO :EOF

:setup_app_env
    ECHO --- Setting up App .env file...
    echo API_BASE_URL=%API_BASE_URL% > .dev.env
GOTO :EOF

:setup_keystore_android
    ECHO --- Setting up Android Keystore...
    copy setup\prebuilt\key.properties android\
GOTO :EOF

:build
    ECHO --- Running common build steps...
    flutter pub get && dart run build_runner build
GOTO :EOF

:build_ios
    ECHO.
    ECHO [WARNING] iOS build steps require a macOS environment with CocoaPods.
    ECHO [WARNING] The 'pod install' command WILL fail on a standard Windows machine.
    ECHO.
    ECHO --- Running iOS-specific build steps...
    flutter pub get
    IF %ERRORLEVEL% NEQ 0 EXIT /B 1

    ECHO --- Changing to 'ios' directory to run 'pod install'...
    pushd ios
    pod install --repo-update
    IF %ERRORLEVEL% NEQ 0 (
        ECHO.
        ECHO [ERROR] 'pod install' failed. This is expected on Windows.
        ECHO Please run this command on a macOS machine with CocoaPods installed.
        popd
        EXIT /B 1
    )
    popd
    dart run build_runner build
GOTO :EOF

:error
    ECHO.
    ECHO [ERROR] %~1
    ECHO.
    ECHO Usage: %~n0 [ios^|android]
    EXIT /B 1
GOTO :EOF

:handle_error
    ECHO.
    ECHO [ERROR] A step in the setup process failed. Exiting.
    EXIT /B 1
GOTO :EOF