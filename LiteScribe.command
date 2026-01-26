#!/bin/bash
# LiteScribe Launcher
# Double-click this file to transcribe audio files

cd "$(dirname "$0")"
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
