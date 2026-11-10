# LiteType

A lightweight, unobtrusive, 100% local voice dictation tool for macOS. Hold a hotkey, speak, release — your words appear at the cursor in any app.

**Privacy first.** No audio or text ever leaves your machine. No accounts, no cloud, no network connections.

---

## Features

- **System-wide dictation** triggered by a customisable hotkey (default: `Fn+Ctrl`)
- **Powered by Whisper** (via `whisper.cpp`) — high accuracy, runs entirely on-device
- **Clipboard safe** — saves and restores your clipboard around every paste
- **Custom vocabulary** — teach it names and acronyms it should spell correctly
- **Menu bar recovery** — re-paste your last few transcriptions (kept in memory only, never saved)
- **Model switcher** — swap Whisper models from the menu bar
- **Microphone choice** — pick which mic LiteType uses, independent of the macOS default
- **Start at login** — runs quietly in the background, no Terminal window
- **Voice shutdown** — say *"LiteType shut down"* while recording to quit hands-free
- **macOS 12.0+**

---

## Install (about 10 minutes)

You'll need a Mac running macOS 12 or newer, an internet connection for setup, and about 1 GB of free space. After setup, LiteType works completely offline.

### 1. Install Python (skip if you already have Python 3.11 or newer)

1. Go to **[python.org/downloads](https://www.python.org/downloads/)** and click the yellow **Download Python** button.
2. Open the downloaded installer and click through it, accepting the defaults.

Not sure if you have it? Skip this step: Setup checks for you, and opens the download page if you need it.

### 2. Download LiteType

1. On this page, click the green **Code** button, then **Download ZIP**.
2. Open your **Downloads** folder and double-click the ZIP to unzip it.
3. Move the `LiteVTT_local-main` folder somewhere permanent, such as your **Documents** folder. LiteType runs from this folder, so don't delete it afterwards.

### 3. Run Setup

1. Open the `LiteVTT_local-main` folder and double-click **`Setup.command`**.
2. macOS will probably say it **can't be opened** because it's from an unidentified developer. This is normal for scripts downloaded from the internet:
   - Click **Done** (or **OK**).
   - Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the message about `Setup.command`.
   - Confirm with **Open Anyway** again and enter your Mac password if asked.
3. A Terminal window opens and installs everything. When asked which model to download, type **2** (Small English, recommended) and press Return.
4. When you see **Setup Complete!**, press Return to close the window.

### 4. Start LiteType

1. Double-click **`LiteType.command`** in the same folder. If macOS blocks it the first time, use **Open Anyway** again as in step 3.
2. A Terminal window opens. Leave it open while you use LiteType. After a few seconds, a **🎙️** icon appears in the menu bar at the top-right of your screen.
3. **Grant permissions.** The first time, macOS asks for two permissions for **Terminal**. Both are required:
   - **Microphone**: click **Allow** when prompted.
   - **Accessibility** (needed to paste text): open **System Settings → Privacy & Security → Accessibility**, turn on **Terminal**, then quit and reopen LiteType.

### 5. Dictate

1. Click into any app where you'd type: a document, email or chat box.
2. **Hold Fn + Ctrl**, speak a sentence or two, then **let go**.
3. Your words appear at the cursor a moment later.

**Tips:**
- Click 🎙️ in the menu bar for more options: re-paste a recent transcription, choose your **Microphone**, switch models, or turn on **Start at Login** so you don't need the Terminal window.
- If you use Bluetooth earbuds, choose a different microphone in the **Microphone** menu. Earbud mics are poor for dictation.
- To quit, click 🎙️ and choose **Quit**.

### For developers

```bash
git clone https://github.com/willbaldlygo/LiteVTT_local.git
cd LiteVTT_local
python3 -m venv venv          # Python 3.11+
source venv/bin/activate
pip install -r requirements.txt
python3 download_models.py
python3 litetype.py
```

Two models are available:
- **Base** (~140 MB): Faster, good for everyday dictation.
- **Small English** (~460 MB): Slightly slower, much more accurate. Recommended.

---

## Configuration

Edit `config.json` to customise behaviour:

| Key | Default | Description |
|-----|---------|-------------|
| `hotkey` | `"Fn+Ctrl"` | Modifier keys to hold while recording. Supported keys: `Fn`, `Ctrl`, `Shift`, `Opt`, `Alt`, `Cmd`. |
| `model.default_model` | `"ggml-base.bin"` | Which model file to load first. |
| `model.use_small_en` | `false` | Set to `true` to prefer the Small English model when available. |
| `microphone` | `[]` | Preferred mics in priority order, matched by part of the name, e.g. `["RODE", "MacBook Pro Microphone"]`. The first one connected is used; if none are, LiteType uses the macOS default input. Empty means always use the macOS default. |
| `vocabulary` | `[]` | Words Whisper should spell correctly, e.g. `["Claude", "AIWP"]`. Restart LiteType after editing. |

Choosing a model from the menu bar's **Model** submenu updates `model.default_model` for you. Choosing a mic from the **Microphone** submenu moves it to the front of `microphone`. Use **Refresh List** there after plugging in a new mic.

> **Bluetooth earbuds:** macOS makes newly connected earbuds your default *input* as well as output. Their mics are poor, and using them switches the earbuds into low-quality headset mode. Choosing another mic in LiteType avoids both.

**Hotkey examples:**

```json
{ "hotkey": "Fn+Ctrl" }
{ "hotkey": "Ctrl+Shift" }
{ "hotkey": "Fn+Opt" }
```

> The hotkey must be a combination of modifier keys only (Fn, Ctrl, Shift, Opt/Alt, Cmd). Regular keys like letters or numbers are not supported.

---

## Start at Login

Choose **Start at Login** in the menu bar menu. From your next login, LiteType starts in the background with no Terminal window. Choose it again to turn it off.

When started this way, macOS asks for permissions on behalf of **Python** rather than Terminal. Allow Python under System Settings → Privacy & Security → **Microphone** and **Accessibility**. LiteType shows "Needs Accessibility permission" in its menu if pasting isn't allowed yet.

Logs are written to `~/Library/Logs/LiteType.log`.

---

## Troubleshooting

**`zsh: command not found: python`** — use `python3`. macOS does not provide a `python` command by default.

**`Setup.command` is blocked by macOS** — open System Settings → Privacy & Security and click **Open Anyway** (see Install, step 3). On older macOS versions, right-click the file and choose **Open** instead. You may need to do the same for `LiteType.command` on first run.

**`pip install` fails with "bad interpreter"** — a stale `venv` from a previous attempt exists. Delete it and start fresh: `rm -rf venv`.

**`No module named ...`** — the virtual environment is not active. Run `source venv/bin/activate` first.

**Setup says Python 3.11 or newer is needed** — install Python from [python.org/downloads](https://www.python.org/downloads/), then run Setup again.

**"Setup.command can't be opened" and there's no Open Anyway button** — try opening it once more, then check System Settings → Privacy & Security again. As a last resort, open Terminal and run `xattr -dr com.apple.quarantine ` followed by a space; then drag the `LiteVTT_local-main` folder into the Terminal window and press Return. This removes macOS's "downloaded from the internet" flag from LiteType's files only.

**Nothing happens when I hold Fn + Ctrl** — check the 🎙️ icon is in the menu bar (on a crowded menu bar, macOS may hide it behind the notch), and that Terminal is allowed under System Settings → Privacy & Security → Accessibility.

**Microphone not working** — open System Settings → Privacy & Security → Microphone and ensure Terminal (or your terminal app) is listed and enabled. Then check which mic is ticked in LiteType's **Microphone** menu.

**Text not pasting** — open System Settings → Privacy & Security → Accessibility and ensure Terminal (or Python, if you use Start at Login) is listed and enabled. If a paste misses, use **Paste Last Transcription** in the menu bar menu.

---

## License & Credits

- **Models**: OpenAI Whisper (MIT License)
- **Inference**: [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- **License**: MIT — see `LICENSE`

---

*Built for speed and privacy.*
