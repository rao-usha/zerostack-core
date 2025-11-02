#!/bin/bash

set -e  # Exit on error

echo "================================================"
echo "  NEX.AI - Complete Setup"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Xcode Command Line Tools are installed
echo "Step 1: Checking Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    echo -e "${RED}❌ Xcode Command Line Tools are NOT installed${NC}"
    echo ""
    echo "IMPORTANT: You need to install Xcode Command Line Tools first!"
    echo ""
    echo "Run this command and follow the prompts:"
    echo "    xcode-select --install"
    echo ""
    echo "After installation completes, run this script again:"
    echo "    ./install_all.sh"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Xcode Command Line Tools installed${NC}"
echo ""

# Check Python
echo "Step 2: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
echo ""

# Install Node.js via nvm
echo "Step 3: Installing Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js already installed: $NODE_VERSION${NC}"
else
    echo "Installing nvm (Node Version Manager)..."
    
    # Install nvm if not present
    if [ ! -d "$HOME/.nvm" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
        echo -e "${GREEN}✅ nvm installed${NC}"
    fi
    
    # Load nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    echo "Installing Node.js LTS..."
    nvm install --lts
    nvm use --lts
    nvm alias default node
    
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js installed: $NODE_VERSION${NC}"
fi
echo ""

# Backend setup
echo "Step 4: Setting up Backend..."
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

echo "Activating virtual environment and installing packages..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo -e "${GREEN}✅ Backend dependencies installed${NC}"
deactivate
cd ..
echo ""

# Frontend setup
echo "Step 5: Setting up Frontend..."
cd "$(dirname "$0")/frontend"

# Make sure nvm is loaded for frontend setup
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Installing frontend packages (this may take a few minutes)..."
npm install

echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
cd ..
echo ""

# Create start scripts
echo "Step 6: Creating convenience scripts..."

# Create backend start script
cat > start_backend.sh << 'BACKEND_SCRIPT'
#!/bin/bash
cd "$(dirname "$0")/backend"
echo "Starting Backend Server..."
source venv/bin/activate
python main.py
BACKEND_SCRIPT
chmod +x start_backend.sh

# Create frontend start script
cat > start_frontend.sh << 'FRONTEND_SCRIPT'
#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "Starting Frontend Server..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
npm run dev
FRONTEND_SCRIPT
chmod +x start_frontend.sh

echo -e "${GREEN}✅ Start scripts created${NC}"
echo ""

# Final instructions
echo "================================================"
echo "  🎉 Installation Complete!"
echo "================================================"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "    ./start_backend.sh"
echo ""
echo "Terminal 2 (Frontend):"
echo "    ./start_frontend.sh"
echo ""
echo "Then open your browser to:"
echo "    ${GREEN}http://localhost:3000${NC}"
echo ""
echo "Quick test with sample data:"
echo "    Upload: example_data/sample_sales_data.csv"
echo ""
echo "For troubleshooting, run:"
echo "    ./check_setup.sh"
echo ""
echo "================================================"

