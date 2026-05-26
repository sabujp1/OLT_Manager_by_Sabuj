@echo off
echo ===================================================
echo          OLT Manager Git Push Utility
echo ===================================================
echo.

:: Check if git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in your system PATH.
    echo Please install Git from https://git-scm.com/ and try again.
    pause
    exit /b
)

:: Initialize Git repository if not already done
if not exist .git (
    echo [1/5] Initializing Git repository...
    git init
) else (
    echo [1/5] Git repository already initialized.
)

:: Stage files
echo [2/5] Staging files...
git add .

:: Commit files
echo [3/5] Committing files...
echo.
git commit -m "Initial commit of OLT NOC Manager"
echo.

:: Setup remote and branch
echo [4/5] Setting up remote and branch...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/sabujp1/OLT_Manager_by_Sabuj.git
git branch -M main

:: Push to remote
echo [5/5] Pushing to GitHub (main branch)...
echo.
git push -u origin main
echo.

echo ===================================================
echo   Push attempt finished!
echo ===================================================
pause
