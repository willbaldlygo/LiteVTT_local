# LiteVTT (Lite Voice-to-Text)

A lightweight, unobtrusive, 100% local voice dictation and transcription for macOS.

## Components
- **LiteType**: System-wide voice dictation triggered by a hotkey (Default: `Fn+Ctrl`). Inserts text directly at your cursor.
- **LiteScribe**: A CLI tool for recording high-quality audio and transcribing existing files (supports `.mp3`, `.m4a`, `.wav`, etc.).

## Features
- **Privacy First**: 100% local processing. No audio or text ever leaves your machine.
- **High Accuracy**: Powered by OpenAI's Whisper (via `whisper.cpp`).
- **Smart Storage**: Automatically archives audio and transcripts. Support for network drive sync with local fallback.
- **Customizable**: Change your hotkeys and storage paths via `config.json`.

---

## 🚀 Quick Start

### 1. Prerequisites
- **macOS 12.0+**
- **Python 3.11+**
- **FFmpeg**: Required for processing different audio formats.
  ```bash
  brew install ffmpeg
  ```

### 2. Installation
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

### 3. Download Models
Run the interactive downloader to get the Whisper models:
```bash
python download_models.py
```
*Choose **Base** for best accuracy or **Small English** for speed.*

---

## 🛠 Usage

### LiteType (Dictation)
Start the menu bar app:
```bash
python litetype.py
```
- **Action**: Hold **`Fn + Ctrl`** to record. Release to transcribe and paste.
- **Voice Shutdown**: Hold **`Fn + Ctrl`** to record, then say *"LiteType shut down"* to close the app via voice.

### LiteScribe (Recording & Files)
```bash
python litescribe.py
```
- **Option 1**: Record new audio directly to your storage folder.
- **Option 2**: Drag and drop any audio file to transcribe it.

---

## ⚙️ Configuration
Edit `config.json` to customize your experience:
- **Hotkeys**: Change the `trigger` (e.g., `Cmd+Shift`).
- **Storage**: Set your `network_volume_prefix` and `folder_name`. Default storage is a local `VTT_Storage` folder in the project root.

---

## 📜 License & Credits
- **Models**: OpenAI Whisper (MIT License).
- **Inference**: Ported via [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov.
- **License**: This project is released under the **MIT License**.

---
*Built with ❤️ for speed and privacy.*
