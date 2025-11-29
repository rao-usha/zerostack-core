#!/bin/bash
cd "$(dirname "$0")/backend"
echo "Starting Backend Server..."
source venv/bin/activate
python main.py
