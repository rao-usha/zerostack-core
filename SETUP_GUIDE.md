# Setup Guide - Getting the Platform Running

## Issue: Nothing Showing at localhost:3000

The frontend requires Node.js to run. Let's get everything set up!

## Step 1: Install Node.js

### On macOS (using Homebrew - Recommended)
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node
```

### On macOS (Direct Download)
1. Go to https://nodejs.org/
2. Download the LTS version for macOS
3. Run the installer
4. Restart your terminal

### Verify Installation
```bash
node --version   # Should show v18.x.x or higher
npm --version    # Should show 9.x.x or higher
```

## Step 2: Install Frontend Dependencies

Once Node.js is installed:
```bash
cd /Users/usharao/Documents/Nex/frontend
npm install
```

This will install all required packages (this may take a few minutes).

## Step 3: Install Backend Dependencies

```bash
cd /Users/usharao/Documents/Nex/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 4: Start the Servers

### Option A: Start Both Separately (Recommended for first time)

**Terminal 1 - Backend:**
```bash
cd /Users/usharao/Documents/Nex/backend
source venv/bin/activate
python main.py
```
You should see: "Application startup complete" and "Uvicorn running on http://0.0.0.0:8000"

**Terminal 2 - Frontend:**
```bash
cd /Users/usharao/Documents/Nex/frontend
npm run dev
```
You should see: "Local: http://localhost:3000"

### Option B: Use the Start Script (After Node.js is installed)
```bash
cd /Users/usharao/Documents/Nex
chmod +x start.sh
./start.sh
```

## Step 5: Access the Application

1. Open your browser
2. Go to: **http://localhost:3000**
3. You should see the AI Native Data Platform dashboard!

## Troubleshooting

### "npm: command not found"
- Node.js is not installed. Follow Step 1 above.

### "Port 3000 already in use"
- Another application is using port 3000
- Kill it: `lsof -ti:3000 | xargs kill -9`
- Or change the port in `frontend/vite.config.ts`

### "Port 8000 already in use"
- Backend is already running or another app is using it
- Kill it: `lsof -ti:8000 | xargs kill -9`

### "Module not found" errors
- Run `npm install` again in the frontend directory
- Run `pip install -r requirements.txt` again in the backend directory

### Blank page at localhost:3000
- Check browser console (F12) for errors
- Make sure backend is running on port 8000
- Check that both servers started successfully

### CORS errors
- Make sure backend is running first
- Check backend logs for CORS configuration

## Quick Check Commands

```bash
# Check if Node.js is installed
node --version

# Check if Python is installed
python3 --version

# Check what's running on port 3000
lsof -i :3000

# Check what's running on port 8000
lsof -i :8000

# Check if dependencies are installed
cd frontend && test -d node_modules && echo "Frontend deps OK" || echo "Run: npm install"
cd ../backend && test -d venv && echo "Backend venv OK" || echo "Run: python3 -m venv venv"
```

## After Setup

Once everything is running:
1. Go to http://localhost:3000
2. Click "Upload Data" in the sidebar
3. Upload the sample file: `example_data/sample_sales_data.csv`
4. Start exploring the platform!

