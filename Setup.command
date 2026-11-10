#!/bin/bash
# LiteType Setup Script

# Move to the script's directory so all relative paths work correctly
cd "$(dirname "$0")"

echo "=========================================="
echo "      LiteType - First Time Setup"
echo "=========================================="
echo ""

# LiteType needs Python 3.11 or newer. Many Macs only have Apple's older
# Python 3.9, which can't run it, so look for a suitable one explicitly.
python_ok() {
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
}

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3 \
                 /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1 && python_ok "$candidate"; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ LiteType needs Python 3.11 or newer, and it isn't installed."
    echo ""
    echo "   1. Download the macOS installer from https://www.python.org/downloads/"
    echo "   2. Open it and click through the installer."
    echo "   3. Then run this Setup again."
    echo ""
    open "https://www.python.org/downloads/" 2>/dev/null
    read -p "Press Enter to close..."
    exit 1
fi
echo "✅ Using $("$PYTHON" --version)"

# 1. Create Virtual Environment (rebuild it if it was made with an old Python)
if [ -d "venv" ] && ! python_ok venv/bin/python; then
    echo "♻️  Existing environment uses an old Python - rebuilding it..."
    rm -rf venv
fi
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    "$PYTHON" -m venv venv || { echo "❌ Could not create the virtual environment."; read -p "Press Enter to close..."; exit 1; }
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists, skipping."
fi

# 2. Install Dependencies
echo ""
echo "📥 Installing dependencies (this can take a few minutes)..."
source venv/bin/activate
pip install --upgrade pip --quiet
if ! pip install -r requirements.txt; then
    echo ""
    echo "❌ Installing dependencies failed. Check your internet connection and run Setup again."
    read -p "Press Enter to close..."
    exit 1
fi
echo "✅ Dependencies installed."

# 3. Download Models
echo ""
echo "🤖 Model Setup"
python download_models.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "You can now double-click LiteType.command to start dictating."
echo "=========================================="
read -p "Press Enter to close..."
