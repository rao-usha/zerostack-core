# Complete Installation Guide

## Prerequisites

Before running the installation script, you need:

1. **Xcode Command Line Tools** (for macOS)
2. **Python 3.8+** (usually comes with macOS)
3. **Internet connection** (for downloading packages)

## Installation Steps

### Step 1: Install Xcode Command Line Tools

This is **REQUIRED** for everything else to work.

```bash
xcode-select --install
```

A dialog will appear:
1. Click "Install"
2. Wait 5-10 minutes for it to complete
3. Click "Done" when finished

To verify installation:
```bash
xcode-select -p
# Should show: /Library/Developer/CommandLineTools
```

### Step 2: Run the Complete Installation Script

Once Xcode tools are installed, run:

```bash
cd /Users/usharao/Documents/Nex
./install_all.sh
```

This script will automatically:
- ✅ Check system requirements
- ✅ Install Node.js (via nvm)
- ✅ Create Python virtual environment
- ✅ Install all backend dependencies
- ✅ Install all frontend dependencies
- ✅ Create convenience start scripts

**Installation will take 5-10 minutes** depending on your internet speed.

### Step 3: Start the Application

After installation completes, start both servers:

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

### Step 4: Access the Platform

Open your browser and go to:
```
http://localhost:3000
```

You should see the AI Native Data Platform dashboard!

## What Gets Installed

### Backend Dependencies
- FastAPI - Web framework
- Pandas - Data manipulation
- Scikit-learn - Machine learning
- NumPy, SciPy - Numerical computing
- SQLAlchemy - Database ORM
- And more (see `backend/requirements.txt`)

### Frontend Dependencies
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- Axios - HTTP client
- React Router - Navigation
- Lucide React - Icons
- And more (see `frontend/package.json`)

## Quick Test

1. Go to "Upload Data" in the sidebar
2. Upload `example_data/sample_sales_data.csv`
3. Navigate to "Insights" to see AI-generated analysis
4. Try the "Chat" feature to ask questions about your data

## Convenience Scripts

After installation, you'll have these scripts:

- `install_all.sh` - Complete installation
- `start_backend.sh` - Start backend server only
- `start_frontend.sh` - Start frontend server only
- `check_setup.sh` - Check installation status
- `install_node.sh` - Install Node.js only

## Troubleshooting

### "xcode-select: error: tool 'xcode-select' requires Xcode"

The Xcode Command Line Tools aren't installed. Run:
```bash
xcode-select --install
```

### "command not found: npm" after installation

Node.js needs to be loaded. Run:
```bash
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
```

Or add to your `~/.zshrc`:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

### Backend won't start - "No module named 'fastapi'"

The virtual environment isn't activated. Use the start script:
```bash
./start_backend.sh
```

Or manually:
```bash
cd backend
source venv/bin/activate
python main.py
```

### Port already in use errors

Kill existing processes:
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Check installation status

Run the diagnostic script:
```bash
./check_setup.sh
```

This will show what's installed and what's missing.

## Manual Installation (Alternative)

If the automatic script doesn't work, you can install manually:

### Backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend:
```bash
# Install Node.js from https://nodejs.org/
cd frontend
npm install
```

## Uninstallation

To remove installed packages:

```bash
# Remove backend virtual environment
rm -rf backend/venv

# Remove frontend packages
rm -rf frontend/node_modules

# Remove Node.js (if installed via nvm)
rm -rf ~/.nvm
```

## Need Help?

1. Run `./check_setup.sh` to diagnose issues
2. Check `SETUP_GUIDE.md` for detailed troubleshooting
3. Review error messages in terminal output

## Next Steps After Installation

1. Upload your data
2. Generate insights
3. Build predictive models
4. Chat with your data
5. Check data quality
6. Identify knowledge gaps
7. Generate synthetic data

Enjoy your AI-powered data platform! 🚀

