# LiteVTT (Lite Voice-to-Text)

A lightweight, unobtrusive, 100% local voice dictation and transcription for macOS.

## Components
- **LiteType**: System-wide voice dictation triggered by a hotkey (`Fn+Ctrl`). Inserts text directly at your cursor.
- **LiteScribe**: A CLI tool for recording audio and transcribing existing files (supports `.mp3`, `.m4a`, `.wav`, and more).

## Features
- **Privacy First**: 100% local processing. No audio or text ever leaves your machine.
- **High Accuracy**: Powered by OpenAI's Whisper (via `whisper.cpp`).
- **Automatic Storage**: Archives audio and transcripts to `~/Documents/LiteVTT/` by default (configurable in `config.json`).
- **Clipboard Safe**: The clipboard is temporarily used during paste but restored to its original contents afterward.

---

## Quick Start

### Option A: One-Click Setup (Recommended)
Double-click **`Setup.command`** in Finder. It will create a virtual environment, install dependencies, and prompt you to download a model.

### Option B: Manual Setup

#### 1. Prerequisites
- **macOS 12.0+**
- **Python 3.11+**
- **FFmpeg**: Required for processing different audio formats.
  ```bash
  brew install ffmpeg
  ```

#### 2. Installation
```bash
# Clone the repository
git clone https://github.com/willbaldlygo/LiteVTT_local.git
cd LiteVTT_local

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Download a Model
Run the interactive downloader:
```bash
python download_models.py
```

Two models are available:
- **Base** (~140 MB): Faster and lighter. Good for most use cases.
- **Small English** (~460 MB): Slower but more accurate. Recommended for better transcription quality.

---

## Usage

### LiteType (Dictation)
Start the menu bar app:
```bash
python litetype.py
```
- **Action**: Hold **`Fn + Ctrl`** to record. Release to transcribe and paste.
- **Voice Shutdown**: Say *"LiteType shut down"* while recording to close the app via voice.

### LiteScribe (Recording & Files)
```bash
python litescribe.py
```
- **Option 1**: Record new audio directly to your storage folder.
- **Option 2**: Drag and drop any audio file to transcribe it.

---

## Configuration
Edit `config.json` to customize behaviour:
- **Storage**: Set `storage.path` to override the default `~/Documents/LiteVTT/`. Leave empty to use the default.
- **Model**: Set `model.default_model` to choose which model to load, or set `model.use_small_en` to `true` to prefer the small English model when available.

Note: The hotkey (`Fn+Ctrl`) is hardcoded and cannot be changed via `config.json`.

---

## License & Credits
- **Models**: OpenAI Whisper (MIT License).
- **Inference**: Ported via [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov.
- **License**: This project is released under the **MIT License**.

---
*Built for speed and privacy.*
