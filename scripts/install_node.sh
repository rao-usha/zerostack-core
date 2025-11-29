#!/bin/bash

echo "=== Installing Node.js for NEX.AI ==="
echo ""

# Check if Xcode Command Line Tools are installed
if ! xcode-select -p &> /dev/null; then
    echo "⚠️  Xcode Command Line Tools are required"
    echo "   A dialog should have appeared - please complete the installation"
    echo "   If no dialog appeared, run: xcode-select --install"
    echo ""
    echo "   After installation completes, run this script again."
    exit 1
fi

echo "✅ Xcode Command Line Tools found"
echo ""

# Install nvm (Node Version Manager)
echo "Installing nvm (Node Version Manager)..."
if [ -d "$HOME/.nvm" ]; then
    echo "✅ nvm already installed"
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    
    # Source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    echo "✅ nvm installed"
fi

# Load nvm in current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

echo ""
echo "Installing Node.js LTS version..."
nvm install --lts
nvm use --lts
nvm alias default node

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Verifying installation..."
node --version
npm --version

echo ""
echo "✅ Node.js is now installed!"
echo ""
echo "Next steps:"
echo "1. Install frontend dependencies:"
echo "   cd frontend && npm install"
echo ""
echo "2. Start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "Note: If you open a new terminal, you may need to run:"
echo "   source ~/.nvm/nvm.sh"
echo "   Or add it to your ~/.zshrc file"

