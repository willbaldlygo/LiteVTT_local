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

## Install

**Prerequisites**
- macOS 12.0+
- Python 3.11+ — verify with `python3 --version`

Install straight from GitHub (a virtual environment is recommended):

```bash
python3 -m venv ~/.venvs/litetype
source ~/.venvs/litetype/bin/activate
pip install git+https://github.com/willbaldlygo/LiteVTT_local.git
```

This installs two commands: `litetype` (the app) and `litetype-download-models`.

### Download a model

```bash
litetype-download-models
```

Models are saved to `~/.local/share/litetype/models/`. Two are available:
- **Base** (~140 MB): Faster, good for everyday dictation.
- **Small English** (~460 MB): Slower, noticeably more accurate.

---

## Usage

```bash
litetype
```

A microphone icon (`🎙️`) appears in your menu bar when LiteType is ready.

- **Hold** your hotkey to start recording.
- **Release** to transcribe and insert the text at your cursor.
- Say *"LiteType shut down"* while recording to quit hands-free.
- macOS will prompt for **Microphone** and **Accessibility** access on first run — both are required.

> Tip: to launch it without keeping a terminal open, keep the virtualenv active in a login item, or create a small `.command` wrapper that activates the venv and runs `litetype`.

---

## Configuration

A config file is created on first run at `~/.config/litetype/config.json`. Edit it to customise behaviour:

| Key | Default | Description |
|-----|---------|-------------|
| `hotkey` | `"Fn+Ctrl"` | Modifier keys to hold while recording. Supported keys: `Fn`, `Ctrl`, `Shift`, `Opt`, `Alt`, `Cmd`. |
| `model.default_model` | `"ggml-base.bin"` | Which model file to load first. |
| `model.use_small_en` | `false` | Set to `true` to prefer the Small English model when available. |

> Paths follow the XDG convention: set `XDG_CONFIG_HOME` / `XDG_DATA_HOME` to relocate the config file or model directory.

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

**`command not found: litetype`** — the virtual environment you installed into is not active. Run `source ~/.venvs/litetype/bin/activate` first.

**`No model — run litetype-download-models`** in the menu bar — you haven't downloaded a model yet. Run `litetype-download-models`.

**Microphone not working** — open System Settings → Privacy & Security → Microphone and ensure Terminal (or your terminal app) is listed and enabled.

**Text not pasting** — open System Settings → Privacy & Security → Accessibility and ensure Terminal is listed and enabled.

---

## License & Credits

- **Models**: OpenAI Whisper (MIT License)
- **Inference**: [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- **License**: MIT — see `LICENSE`

---

*Built for speed and privacy.*
