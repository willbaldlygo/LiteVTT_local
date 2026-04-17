#!/usr/bin/env python3
"""
LiteScribe - Recording & Transcription Tool
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import shlex
from vtt.recorder import LiteRecorder
from vtt.transcriber import Transcriber

def convert_to_wav(input_path):
    """Convert audio file to 16kHz mono WAV using ffmpeg. Returns path to temp WAV file."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
    os.close(temp_fd)

    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', '16000',  # Resample to 16kHz for Whisper
            '-ac', '1',      # Convert to mono
            temp_path
        ], check=True, capture_output=True)
        return temp_path
    except subprocess.CalledProcessError as e:
        os.unlink(temp_path)
        raise RuntimeError(f"ffmpeg conversion failed: {e.stderr.decode()}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
    return {}

def get_model_path(config):
    """Determine which model to load based on config and available files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(project_root, "models")
    model_cfg = config.get("model", {})
    use_small_en = model_cfg.get("use_small_en", False)
    default_model = model_cfg.get("default_model", "ggml-base.bin")

    if use_small_en:
        candidates = ["ggml-small.en.bin", "ggml-base.en.bin", "ggml-base.bin"]
    else:
        candidates = [default_model, "ggml-base.en.bin", "ggml-small.en.bin", "ggml-base.bin"]

    # Deduplicate while preserving order
    seen = set()
    candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    for name in candidates:
        path = os.path.join(models_dir, name)
        if os.path.exists(path):
            return path, name

    return None, None

def get_transcriber(model_path):
    print("Loading model...", end="\r")
    return Transcriber(model_path)

def mode_record(recorder, transcriber):
    print("\n--- RECORDING MODE ---")
    print("Press Enter to START recording...")
    input()

    print("🔴 RECORDING... (Press Enter to STOP)")
    try:
        recorder.start()
        input()
    finally:
        print("Stopping...", end="\r")
        audio = recorder.stop()

    print("✅ Recording stopped.")

    if audio is None or len(audio) == 0:
        print("No audio recorded.")
        return

    # Save Audio
    try:
        full_path, filename = recorder.save(audio)
        print(f"\nSaved Audio: {filename}")
    except Exception as e:
        print(f"Error saving audio: {e}")
        return

    # Transcribe
    print("Transcribing...", end="\r")
    try:
        text = transcriber.transcribe(audio)
        print("\n--- TRANSCRIPT ---")
        print(text)
        print("------------------")

        # Save Transcript
        txt_path = recorder.save_transcript(text, filename)
        print(f"Saved Transcript: {os.path.basename(txt_path)}")

    except Exception as e:
        print(f"Error transcribing: {e}")

def mode_transcribe_file(recorder, transcriber):
    print("\n--- FILE TRANSCRIPTION MODE ---")
    print("Drag and drop an audio file here:")
    raw_input = input("> ").strip()

    # Use shlex to handle escaped spaces and quotes from terminal drag-and-drop
    try:
        parts = shlex.split(raw_input)
        if not parts:
            print("No file provided.")
            return
        file_path = parts[0]
    except ValueError:
        # Fallback for malformed input
        file_path = raw_input.replace("'", "").replace('"', "")

    if not os.path.exists(file_path):
        print("File not found.")
        return

    print("Transcribing file...", end="\r")

    try:
        import shutil
        import soundfile as sf
        import numpy as np

        filename = os.path.basename(file_path)

        # Archive original file
        if not recorder.base_path:
            recorder.base_path = recorder._find_storage_path()

        if recorder.base_path:
            save_dir = os.path.join(recorder.base_path, "Recordings")
            os.makedirs(save_dir, exist_ok=True)
            dest_path = os.path.join(save_dir, filename)

            if os.path.abspath(file_path) != os.path.abspath(dest_path):
                shutil.copy2(file_path, dest_path)
                print(f"Archived audio to: {filename}")

            # Always convert through ffmpeg to guarantee 16kHz mono output
            audio_path = convert_to_wav(file_path)

            try:
                data, _ = sf.read(audio_path)

                # Convert to mono if stereo
                if len(data.shape) > 1:
                    data = data.mean(axis=1)

                data = data.astype(np.float32)

                text = transcriber.transcribe(data)
            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

            print("\n--- TRANSCRIPT ---")
            print(text)
            print("------------------")

            # Save Transcript
            txt_path = recorder.save_transcript(text, filename)
            print(f"Saved Transcript: {os.path.basename(txt_path)}")

        else:
            print("Error: Could not determine a save location for transcripts.")

    except Exception as e:
        print(f"Error: {e}")


def main():
    config = load_config()

    # Setup recorder
    recorder = LiteRecorder()
    print(f"📂 Storage: {recorder.base_path}")

    # Model selection
    model_path, model_name = get_model_path(config)

    if not model_path:
        print("❌ No model found. Please run 'python download_models.py' first.")
        return

    print(f"✨ Using model: {model_name}")

    transcriber = get_transcriber(model_path)

    while True:
        print("\nLiteScribe Audio Tool")
        print("1. Record New Audio")
        print("2. Transcribe Existing File")
        print("3. Quit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            mode_record(recorder, transcriber)
        elif choice == "2":
            mode_transcribe_file(recorder, transcriber)
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

        print("\nPress Enter to continue...")
        input()
        clear_screen()

if __name__ == "__main__":
    main()
