#!/bin/bash
# Download Upgrade Model (Small English)
# Improves accuracy significantly (~466MB)

cd "$(dirname "$0")"
mkdir -p models

echo "========================================================"
echo "    LiteType - Model Downloader"
echo "========================================================"
echo ""
echo "Downloading 'ggml-small.en.bin'..."
echo "This model (Small.en) is much smarter than the base model."
echo ""

curl -L -o models/ggml-small.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Download complete!"
    echo "Restart LiteType to apply changes."
else
    echo ""
    echo "❌ Download failed."
fi

echo ""
echo "Press Enter to close..."
read
