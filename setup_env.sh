#!/bin/bash
# Setup script for CS2 Heightmap Generator (macOS/Linux)
# Creates virtual environment and installs dependencies

set -e

echo "========================================="
echo "CS2 Heightmap Generator - Setup"
echo "========================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/3] Checking Python version..."
python3 --version

echo
echo "[2/3] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation."
else
    python3 -m venv venv
    echo "Virtual environment created successfully."
fi

echo
echo "[3/3] Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo
echo "To activate the virtual environment, run:"
echo "    source venv/bin/activate"
echo
echo "To generate your first map, run:"
echo "    python generate_map.py"
echo
echo "For examples, see the examples/ folder."
echo
