#!/bin/bash
# Setup script for Test Planning Helper development environment

# Detect the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows"
    PYTHON_CMD="python"
else
    echo "Unknown operating system. Assuming python3 is available."
    PYTHON_CMD="python3"
fi

# Navigate to the repo root
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Check for Python
echo "Checking for Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python $PYTHON_VERSION"

# Minimum Python version check
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    echo "Python 3.8 or higher is required."
    exit 1
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
cd "$ROOT_DIR"
$PYTHON_CMD -m venv .venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd "$ROOT_DIR/backend"
pip install --upgrade pip
pip install -r requirements.txt

# Optional: Install development tools
pip install black isort mypy pytest

echo ""
echo "Development environment setup complete!"
echo ""
echo "To activate the virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  source .venv/Scripts/activate"
else
    echo "  source .venv/bin/activate"
fi
echo ""
echo "To run the backend server:"
echo "  cd backend"
echo "  uvicorn app.main:app --reload" 