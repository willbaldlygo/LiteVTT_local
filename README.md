## Components
- **LiteType**: System-wide voice dictation via `Fn+Ctrl` hotkey
- **LiteScribe**: Drag-and-drop file transcription

## Features
- 100% local processing - no data leaves your Mac
- Menu bar app with status indicators

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download Whisper model
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# Run LiteType
python run.py
```

## Improving Accuracy
If you find the dictation misses words, double-click `download_model.command` to upgrade to the smarter **Small** model (~466MB).

## Start at Login
To run LiteType automatically when you log in:
1. Double-click `install_startup.command`
2. Follow the prompt.

## Usage: LiteType (Dictation)
1. Double-click `LiteType.command` to start
2. Hold **`Fn+Ctrl`** to start recording
3. Speak your text (Release to paste)

**Voice Shutdown**:
Say "LiteType shut down" to close the app via voice.

## Usage: LiteScribe (Recording & Transcription)
1. Double-click `LiteScribe.command`
2. Choose a mode:
   - **[1] Record New Audio**: Records to WAV and auto-transcribes
   - **[2] Transcribe Existing File**: Drag-and-drop a file

**Storage**:
Files are automatically saved to your network drive (`array_main/Lite_VTT`) if mounted.
- Audio: `/Lite_VTT/Lite_Scribe_Audio/`
- Text:  `/Lite_VTT/Lite_Scribe_Transcripts/`
2. Hold `Option+` ` (backtick) to start recording
3. Speak your text
4. Release key to transcribe and insert text at cursor

## Usage: File Transcription
You can transcribe audio files (wav, mp3, m4a, etc.) via the command line:

```bash
cd /Users/will/VTT_local
source venv/bin/activate

# Print to screen
python transcribe.py my_audio.wav

# Save to file
python transcribe.py my_audio.wav -o transcript.txt
```

## Requirements
- macOS 12+
- Python 3.11+
- Microphone access permission
- Accessibility permission (for hotkeys and text insertion)
