@echo off
setlocal ENABLEDELAYEDEXPANSION

title TreesBot Build System
color 0A

echo ======================================================
echo        TreesBot Command Center - Build System 🚀
echo ======================================================
echo.

:: -------------------------------
:: CONFIG
:: -------------------------------
set APP_NAME=TreesBot_Dashboard
set SPEC_FILE=TreesBot_Dashboard.spec
set DIST_DIR=dist
set BUILD_DIR=build

:: -------------------------------
:: CHECK PYTHON
:: -------------------------------
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b
)

:: -------------------------------
:: CHECK SPEC FILE
:: -------------------------------
if not exist %SPEC_FILE% (
    echo [ERROR] %SPEC_FILE% not found
    pause
    exit /b
)

:: -------------------------------
:: CLEAN OLD BUILD
:: -------------------------------
echo.
echo [0/3] Cleaning old build...
taskkill /f /im %APP_NAME%.exe >nul 2>&1

if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%
if exist __pycache__ rmdir /s /q __pycache__

echo [OK] Clean complete

:: -------------------------------
:: BUILD MODE
:: -------------------------------
echo.
echo Select build mode:
echo 1 = DEV (Console ON - for debugging)
echo 2 = RELEASE (No Console - clean app experience)
set /p MODE=Choose (1/2): 

if "%MODE%"=="1" (
    set PYI_CONSOLE=True
    echo [MODE] DEV (Console Enabled)
) else (
    set PYI_CONSOLE=False
    echo [MODE] RELEASE (Console Hidden)
)

:: -------------------------------
:: BUILD START
:: -------------------------------
echo.
echo [1/3] Building EXE using Dynamic Spec...
echo.

:: Run PyInstaller using the SPEC file (NO conflicting flags)
python -m PyInstaller --clean %SPEC_FILE%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build FAILED. Please check the logs above.
    pause
    exit /b %ERRORLEVEL%
)

:: -------------------------------
:: VERIFY OUTPUT
:: -------------------------------
echo.
echo [2/3] Verifying output...

if exist %DIST_DIR%\%APP_NAME%.exe (
    echo [OK] EXE created successfully
) else (
    echo [ERROR] EXE not found in %DIST_DIR%
    pause
    exit /b
)

:: -------------------------------
:: FINAL & PACKAGING
:: -------------------------------
echo.
echo [3/3] Packaging Application...

set PKG_DIR=%DIST_DIR%\TreesBot_App_v1.0.0

if not exist %PKG_DIR% mkdir %PKG_DIR%
move /y %DIST_DIR%\%APP_NAME%.exe %PKG_DIR%\ >nul
copy /y Create_Shortcut.bat %PKG_DIR%\ >nul

echo.
echo ======================================================
echo  ✨ BUILD & PACKAGING SUCCESSFUL!
echo ======================================================
echo.
echo  [Step 1] Go to: %PKG_DIR%
echo  [Step 2] Right-click %APP_NAME%.exe -> "Create Shortcut"
echo  [Step 3] Drag that shortcut to your Desktop!
echo.
echo  (All system files will now stay inside the folder)
echo ======================================================
echo.
pause