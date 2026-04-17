#!/bin/bash
# LiteVTT Setup Script

# Move to the script's directory so all relative paths work correctly
cd "$(dirname "$0")"

echo "=========================================="
echo "      LiteVTT - First Time Setup"
echo "=========================================="
echo ""

# 1. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists, skipping."
fi

# 2. Install Dependencies
echo ""
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "✅ Dependencies installed."

# 3. Download Models
echo ""
echo "🤖 Model Setup"
python download_models.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "You can now open LiteType.command or LiteScribe.command"
echo "=========================================="
read -p "Press Enter to close..."
