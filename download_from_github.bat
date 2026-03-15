@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Download and Sync Script
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed
    echo Please download Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Git is installed
echo.

REM Configuration
set REPO_URL=https://github.com/ShakeHsu/The-Current-Catcher.git
set LOCAL_DIR=C:\Users\XU\Documents\trae_projects\The Current Catcher

echo Repository URL: %REPO_URL%
echo Local Directory: %LOCAL_DIR%
echo.

REM Change to directory
cd /d "%LOCAL_DIR%"

REM Check if already a Git repository
if exist .git (
    echo Repository exists, pulling latest code...
    git pull origin main
    if %errorlevel% equ 0 (
        echo SUCCESS: Code updated to latest version
    ) else (
        echo ERROR: Pull failed, check network connection
    )
) else (
    echo Cloning repository...
    git clone %REPO_URL%
    if %errorlevel% equ 0 (
        echo SUCCESS: Repository cloned
        cd The-Current-Catcher
    ) else (
        echo ERROR: Clone failed, check network or repo URL
    )
)

echo.
echo ========================================
echo Current directory: %cd%
echo ========================================
echo.

REM Show file list
echo File list:
dir /b

echo.
echo ========================================
echo Done! You can start working now.
echo ========================================
echo.
echo After modifying code, use these commands:
echo   git add .
echo   git commit -m "description"
echo   git push
echo.
pause