#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "Starting Frontend Server..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
npm run dev
