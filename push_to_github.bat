@echo off
echo ========================================================
echo  AI TRADING BOT - GITHUB SYNC HELPER
echo ========================================================
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed on your system!
    echo Please download and install Git from: https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b
)

echo [1/4] Initializing Git repository...
if not exist ".git" (
    git init
    git branch -M main
)

echo [2/4] Staging files (Note: .env and private keys are ignored!)...
git add .

echo [3/4] Creating commit...
git commit -m "feat: AI Intraday Trading Bot with Price Action & Paper Trading"

echo.
set /p REPO_URL="Enter your GitHub Repository URL (or press Enter to skip push): "
if not "%REPO_URL%"=="" (
    git remote remove origin >nul 2>nul
    git remote add origin %REPO_URL%
    echo [4/4] Pushing to GitHub...
    git push -u origin main
    echo.
    echo [SUCCESS] Code pushed to GitHub safely!
) else (
    echo Staged and committed locally. You can push anytime later.
)

pause
