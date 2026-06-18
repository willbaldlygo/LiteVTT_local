# LiteType

A lightweight, unobtrusive, 100% local voice dictation tool for macOS. Hold a hotkey, speak, release — your words appear at the cursor in any app.

**Privacy first.** No audio or text ever leaves your machine. No accounts, no cloud, no network connections.

---

## Features

- **System-wide dictation** triggered by a customisable hotkey (default: `Fn+Ctrl`)
- **Powered by Whisper** (via `whisper.cpp`) — high accuracy, runs entirely on-device
- **Clipboard safe** — saves and restores your clipboard around every paste
- **Voice shutdown** — say *"LiteType shut down"* while recording to quit hands-free
- **macOS 12.0+**

---

## Quick Start

### Option A: One-Click Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/willbaldlygo/LiteVTT_local.git
   cd LiteVTT_local
   ```
2. **Right-click** `Setup.command` and choose **Open** (required on first run — macOS blocks a direct double-click from an unrecognised developer).
3. Click **Open** again in the security prompt.
4. The script creates a virtual environment, installs dependencies, and walks you through downloading a model.

### Option B: Manual Setup

**Prerequisites**
- macOS 12.0+
- Python 3.11+ — verify with `python3 --version`

```bash
git clone https://github.com/willbaldlygo/LiteVTT_local.git
cd LiteVTT_local
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 download_models.py
```

Two models are available:
- **Base** (~140 MB): Faster, good for everyday dictation.
- **Small English** (~460 MB): Slower, noticeably more accurate.

---

## Usage

Double-click **`LiteType.command`** in Finder, or from a terminal:

```bash
source venv/bin/activate
python3 litetype.py
```

A microphone icon (`🎙️`) appears in your menu bar when LiteType is ready.

- **Hold** your hotkey to start recording.
- **Release** to transcribe and insert the text at your cursor.
- macOS will prompt for **Microphone** and **Accessibility** access on first run — both are required.

---

## Configuration

Edit `config.json` to customise behaviour:

| Key | Default | Description |
|-----|---------|-------------|
| `hotkey` | `"Fn+Ctrl"` | Modifier keys to hold while recording. Supported keys: `Fn`, `Ctrl`, `Shift`, `Opt`, `Alt`, `Cmd`. |
| `model.default_model` | `"ggml-base.bin"` | Which model file to load first. |
| `model.use_small_en` | `false` | Set to `true` to prefer the Small English model when available. |

**Hotkey examples:**

```json
{ "hotkey": "Fn+Ctrl" }
{ "hotkey": "Ctrl+Shift" }
{ "hotkey": "Fn+Opt" }
```

> The hotkey must be a combination of modifier keys only (Fn, Ctrl, Shift, Opt/Alt, Cmd). Regular keys like letters or numbers are not supported.

---

## Troubleshooting

**`zsh: command not found: python`** — use `python3`. macOS does not provide a `python` command by default.

**`Setup.command` is blocked by macOS** — right-click it and choose Open instead of double-clicking. You may need to do the same for `LiteType.command` on first run.

**`pip install` fails with "bad interpreter"** — a stale `venv` from a previous attempt exists. Delete it and start fresh: `rm -rf venv`.

**`No module named ...`** — the virtual environment is not active. Run `source venv/bin/activate` first.

**Microphone not working** — open System Settings → Privacy & Security → Microphone and ensure Terminal (or your terminal app) is listed and enabled.

**Text not pasting** — open System Settings → Privacy & Security → Accessibility and ensure Terminal is listed and enabled.

---

## License & Credits

- **Models**: OpenAI Whisper (MIT License)
- **Inference**: [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- **License**: MIT — see `LICENSE`

---

*Built for speed and privacy.*
