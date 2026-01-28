#!/bin/bash
# LiteScribe Launcher
# Double-click this file to transcribe audio files

PROJECT_DIR="/Users/will/VTT_local"
cd "$PROJECT_DIR"
source venv/bin/activate

echo "========================================================"
echo "    LiteScribe - File Transcriber"
echo "========================================================"
echo ""
python litescribe.py

echo ""
echo "========================================================"
echo "Done! Press Enter to close this window..."
read
