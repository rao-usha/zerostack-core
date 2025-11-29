# 🚀 NEX.AI - START HERE - Quick Setup

## Current Status
❌ **Xcode Command Line Tools** - Not installed (REQUIRED)  
❌ **Node.js** - Not installed  
❌ **Dependencies** - Not installed  

## One-Command Installation (After Xcode Tools)

Once Xcode Command Line Tools are ready, just run:

```bash
cd /Users/usharao/Documents/Nex
./install_all.sh
```

This will automatically install everything!

---

## Step-by-Step Instructions

### 1️⃣ Install Xcode Command Line Tools (5-10 minutes)

Run this command:
```bash
xcode-select --install
```

A dialog will appear:
- Click **"Install"**
- Wait for it to finish (grab a coffee ☕)
- Click **"Done"**

### 2️⃣ Install Everything Else (5-10 minutes)

After Xcode tools are done:
```bash
cd /Users/usharao/Documents/Nex
./install_all.sh
```

The script will:
- ✅ Install Node.js
- ✅ Install all backend packages
- ✅ Install all frontend packages
- ✅ Create start scripts

### 3️⃣ Start the Application

**Terminal 1:**
```bash
./start_backend.sh
```

**Terminal 2:**
```bash
./start_frontend.sh
```

### 4️⃣ Open Your Browser

Go to: **http://localhost:3000**

---

## What's Being Installed

### Backend Packages
- FastAPI (web framework)
- Pandas (data analysis)
- Scikit-learn (machine learning)
- NumPy, SciPy (math libraries)
- And 10+ more packages

### Frontend Packages
- React 18 (UI framework)
- TypeScript (programming language)
- Tailwind CSS (styling)
- Vite (build tool)
- And 15+ more packages

**Total download size:** ~300-500 MB  
**Installation time:** 10-15 minutes total

---

## Quick Test

Once running:
1. Click "Upload Data"
2. Upload `example_data/sample_sales_data.csv`
3. Go to "Insights" to see AI analysis
4. Try "Chat" to ask questions about your data

---

## Need Help?

Check if everything is ready:
```bash
./check_setup.sh
```

See detailed guides:
- `INSTALLATION.md` - Complete installation guide
- `SETUP_GUIDE.md` - Troubleshooting
- `README.md` - Full documentation

---

## Why Multiple Steps?

1. **Xcode Command Line Tools** - Required by macOS for development tools
2. **Node.js** - Runs the frontend (React application)
3. **Python packages** - Powers the backend AI/ML features

Without Xcode tools, nothing else can install properly.

---

## TL;DR

```bash
# Step 1: Install Xcode tools (do this once)
xcode-select --install

# Step 2: Install everything (after Xcode completes)
./install_all.sh

# Step 3: Start servers
./start_backend.sh    # Terminal 1
./start_frontend.sh   # Terminal 2

# Step 4: Open browser
open http://localhost:3000
```

That's it! 🎉

