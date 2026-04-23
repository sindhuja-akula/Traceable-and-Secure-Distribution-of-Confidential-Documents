@echo off
echo ======================================================
echo   Secure Document System - Automatic Setup (Windows)
echo ======================================================
echo.

echo [1/4] Installing Frontend Dependencies...
call npm install --prefix frontend
if %errorlevel% neq 0 (
    echo Error installing frontend dependencies.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Creating Python Virtual Environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Error creating virtual environment. Please ensure Python is installed and in your PATH.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/4] Upgrading Pip and Build Tools...
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo Error upgrading pip.
    pause
    exit /b %errorlevel%
)

echo.
echo [4/4] Installing Backend Requirements (including asyncpg)...
.\.venv\Scripts\pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install backend requirements.
    echo.
    echo COMMON FIX for 'asyncpg' error:
    echo 1. Ensure you are using Python 3.10, 3.11, or 3.12.
    echo 2. If using Python 3.13+, you may need Visual Studio Build Tools (C++).
    echo 3. Try running: .\.venv\Scripts\python.exe -m pip install asyncpg==0.29.0
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================================
echo   SETUP COMPLETE!
echo   You can now run: npm start
echo ======================================================
pause
