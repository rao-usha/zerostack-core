# Installing Node.js - Quick Guide

## Current Status

✅ **Xcode Command Line Tools installation has been initiated**

A dialog should have appeared on your screen asking you to install the Command Line Tools. 

## Steps to Complete Installation

### Step 1: Complete Xcode Command Line Tools Installation

1. **If you see a dialog asking to install Command Line Tools:**
   - Click "Install" 
   - Wait for the installation to complete (this may take 5-10 minutes)
   - Click "Done" when finished

2. **If you don't see a dialog, run this command:**
   ```bash
   xcode-select --install
   ```

### Step 2: Install Node.js (After Xcode Tools Complete)

Once the Xcode Command Line Tools are installed, run:

```bash
cd /Users/usharao/Documents/Nex
./install_node.sh
```

This script will:
- Install nvm (Node Version Manager)
- Install the latest LTS version of Node.js
- Set it up for use

### Step 3: Verify Installation

After running the script, verify Node.js is installed:

```bash
node --version   # Should show v20.x.x or similar
npm --version    # Should show 10.x.x or similar
```

### Step 4: Install Frontend Dependencies

```bash
cd /Users/usharao/Documents/Nex/frontend
npm install
```

### Step 5: Start the Frontend

```bash
cd /Users/usharao/Documents/Nex/frontend
npm run dev
```

Then open http://localhost:3000 in your browser!

## Alternative: Manual Installation

If you prefer to install Node.js directly (without nvm):

1. Go to https://nodejs.org/
2. Download the LTS version for macOS
3. Run the installer
4. Restart your terminal
5. Verify: `node --version`

## Troubleshooting

### "nvm: command not found" in new terminals

Add this to your `~/.zshrc` file:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

Then run: `source ~/.zshrc`

### Installation Script Won't Run

Make sure it's executable:
```bash
chmod +x install_node.sh
```

### Still Having Issues?

Run the diagnostic script:
```bash
./check_setup.sh
```

