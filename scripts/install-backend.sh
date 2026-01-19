#!/bin/bash
# ZeroStack Backend Installation Script (Unix/Linux/Mac)
# Usage: ./scripts/install-backend.sh [core|ml|full]

set -e

MODE="${1:-core}"

echo "================================"
echo "ZeroStack Backend Installation"
echo "================================"
echo ""

# Validate mode
if [[ ! "$MODE" =~ ^(core|ml|full)$ ]]; then
    echo "ERROR: Invalid mode '$MODE'"
    echo "Usage: $0 [core|ml|full]"
    echo "  core - Fast install, no ML/PyTorch (default)"
    echo "  ml   - Includes SDV/PyTorch for synthetic data"
    echo "  full - Everything including test dependencies"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.11+"
    exit 1
fi
echo "Found: $(python3 --version)"

# Navigate to backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install based on mode
case "$MODE" in
    "core")
        echo ""
        echo "Installing CORE dependencies (fast, no ML)..."
        echo "This skips PyTorch/SDV for faster install."
        echo ""
        pip install -r requirements-core.txt
        echo ""
        echo "✅ Core install complete!"
        echo "To add ML support later: pip install -r requirements-ml.txt"
        ;;
    "ml")
        echo ""
        echo "Installing ML dependencies (includes PyTorch)..."
        echo "This may take 5-10 minutes."
        echo ""

        # Option: CPU-only PyTorch
        read -p "Use CPU-only PyTorch? (saves ~1.5GB) [Y/n]: " cpu_only
        if [[ ! "$cpu_only" =~ ^[Nn]$ ]]; then
            echo "Installing CPU-only PyTorch first..."
            pip install torch --index-url https://download.pytorch.org/whl/cpu
        fi

        pip install -r requirements-ml.txt
        echo ""
        echo "✅ ML install complete!"
        ;;
    "full")
        echo ""
        echo "Installing FULL dependencies (ML + testing)..."
        echo "This may take 10+ minutes."
        echo ""
        pip install -r requirements.txt
        echo ""
        echo "✅ Full install complete!"
        ;;
esac

echo ""
echo "================================"
echo "Installation Summary"
echo "================================"
echo "Mode: $MODE"
echo "Virtual env: backend/venv"
echo ""
echo "To activate: source backend/venv/bin/activate"
echo "To run server: cd backend && uvicorn main:app --reload"
echo ""
