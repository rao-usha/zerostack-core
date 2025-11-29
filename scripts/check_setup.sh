#!/bin/bash

echo "=== NEX.AI - Setup Checker ==="
echo ""

# Check Node.js
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js installed: $NODE_VERSION"
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo "✅ npm installed: $NPM_VERSION"
    else
        echo "❌ npm not found (should come with Node.js)"
    fi
else
    echo "❌ Node.js NOT installed"
    echo "   Install from: https://nodejs.org/"
    echo "   Or use Homebrew: brew install node"
fi
echo ""

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Python 3 NOT installed"
    echo "   Install from: https://www.python.org/downloads/"
    echo "   Or use Homebrew: brew install python3"
fi
echo ""

# Check ports
echo "Checking ports..."
if lsof -i :3000 &> /dev/null; then
    echo "⚠️  Port 3000 is in use"
    echo "   Frontend may already be running"
else
    echo "✅ Port 3000 is available"
fi

if lsof -i :8000 &> /dev/null; then
    echo "⚠️  Port 8000 is in use"
    echo "   Backend may already be running"
else
    echo "✅ Port 8000 is available"
fi
echo ""

# Check dependencies
echo "Checking dependencies..."
cd "$(dirname "$0")"

if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "❌ Frontend dependencies NOT installed"
    echo "   Run: cd frontend && npm install"
fi

if [ -d "backend/venv" ]; then
    echo "✅ Backend virtual environment exists"
else
    echo "❌ Backend virtual environment NOT created"
    echo "   Run: cd backend && python3 -m venv venv"
fi
echo ""

echo "=== Setup Status ==="
echo ""
echo "To get started:"
echo "1. Install Node.js if missing (see above)"
echo "2. Install Python 3 if missing (see above)"
echo "3. Install dependencies (see commands above)"
echo "4. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "5. Start frontend: cd frontend && npm run dev"
echo ""
echo "See SETUP_GUIDE.md for detailed instructions"

