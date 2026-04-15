#!/bin/bash
# LiteVTT Setup Script

# Move to the script's directory
cd "$(dirname "$0")"

echo "=========================================="
echo "      LiteVTT - First Time Setup"
echo "=========================================="
echo ""

# 1. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Install Dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Download Models
echo ""
echo "🤖 Model Setup"
python3 download_models.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "You can now use LiteType.command or LiteScribe.command"
echo "=========================================="
read -p "Press Enter to close..."
