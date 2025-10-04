@echo off
REM Setup script for CS2 Heightmap Generator
REM Creates virtual environment and installs dependencies

echo =========================================
echo CS2 Heightmap Generator - Setup
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/3] Checking Python version...
python --version

echo.
echo [2/3] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

echo.
echo [3/3] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo =========================================
echo Setup complete!
echo =========================================
echo.
echo To activate the virtual environment, run:
echo    venv\Scripts\activate
echo.
echo To generate your first map, run:
echo    python generate_map.py
echo.
echo For examples, see the examples\ folder.
echo.
pause
