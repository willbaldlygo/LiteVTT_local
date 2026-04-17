#!/bin/bash
# LiteType Launcher

# Move to the script's directory
cd "$(dirname "$0")"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "Please run Setup.command first."
    read -p "Press Enter to exit..."
    exit 1
fi

# Activate and run
source venv/bin/activate
python litetype.py

osascript -e 'tell application "Terminal" to close front window'
