# LiteVTT (Lite Voice-to-Text)

A lightweight, unobtrusive, 100% local voice dictation and transcription tool for macOS.

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

1. Clone or download this repository and open the folder in Finder.
2. **Right-click** `Setup.command` and choose **Open** (required on first run — macOS will block a direct double-click from an unrecognised developer).
3. Click **Open** again in the security prompt.
4. The script will create a virtual environment, install dependencies, and walk you through downloading a model.

### Option B: Manual Setup

#### 1. Prerequisites
- **macOS 12.0+**
- **Python 3.11+** — verify with `python3 --version`
- **FFmpeg** — required for processing audio formats other than WAV:
  ```bash
  brew install ffmpeg
  ```

#### 2. Clone and enter the repository
```bash
git clone https://github.com/willbaldlygo/LiteVTT_local.git
cd LiteVTT_local
```

> **Note:** `git clone` creates a folder called `LiteVTT_local`. The `cd` above puts you inside it. All subsequent commands must be run from this folder.

#### 3. Create a virtual environment and install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Download a model
```bash
python3 download_models.py
```

Two models are available:
- **Base** (~140 MB): Faster and lighter. Good for most use cases.
- **Small English** (~460 MB): Slower but more accurate. Recommended for better transcription quality.

---

## Usage

> All commands below assume the virtual environment is active (`source venv/bin/activate`). Alternatively, use the `.command` launcher files in Finder — they activate the venv automatically.

### LiteType (Dictation)
```bash
python3 litetype.py
```
- Hold **`Fn + Ctrl`** to record. Release to transcribe and paste at the cursor.
- Say *"LiteType shut down"* while recording to quit via voice.
- macOS will prompt for **Microphone** and **Accessibility** access on first run — both are required.

### LiteScribe (Recording & Transcription)
```bash
python3 litescribe.py
```
- **Option 1**: Record new audio directly to your storage folder.
- **Option 2**: Drag and drop any audio file to transcribe it.

---

## Configuration
Edit `config.json` to customise behaviour:
- **Storage**: Set `storage.path` to override the default `~/Documents/LiteVTT/`. Leave empty to use the default.
- **Model**: Set `model.default_model` to choose which model to load, or set `model.use_small_en` to `true` to prefer the Small English model when available.

Note: The hotkey (`Fn+Ctrl`) is hardcoded and cannot be changed via `config.json`.

---

## Troubleshooting

**`zsh: command not found: python`** — use `python3` instead. macOS does not provide a `python` command by default.

**`Setup.command` is blocked by macOS** — right-click it and choose Open instead of double-clicking.

**`pip install` fails with "bad interpreter"** — a stale `venv` folder from a previous attempt is present. Delete it and start fresh: `rm -rf venv`, then re-run the setup steps.

**`No module named ...`** — the virtual environment is not active. Run `source venv/bin/activate` first.

---

## License & Credits
- **Models**: OpenAI Whisper (MIT License).
- **Inference**: Ported via [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov.
- **License**: This project is released under the **MIT License**.

---
*Built for speed and privacy.*
