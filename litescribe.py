#!/usr/bin/env python3
"""
LiteScribe - Recording & Transcription Tool
"""

import os
import sys
import time
import subprocess
import tempfile
import shlex
from vtt.recorder import LiteRecorder
from vtt.transcriber import Transcriber

# Formats that soundfile can read natively
SUPPORTED_FORMATS = {'.wav', '.flac', '.ogg', '.aiff', '.aif'}

def convert_to_wav(input_path):
    """Convert audio file to WAV using ffmpeg. Returns path to temp WAV file."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext in SUPPORTED_FORMATS:
        return input_path, False  # No conversion needed
    
    # Create temp file for converted audio
    temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
    os.close(temp_fd)
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', '16000',  # Resample to 16kHz for Whisper
            '-ac', '1',      # Convert to mono
            temp_path
        ], check=True, capture_output=True)
        return temp_path, True  # Temp file needs cleanup
    except subprocess.CalledProcessError as e:
        os.unlink(temp_path)
        raise RuntimeError(f"ffmpeg conversion failed: {e.stderr.decode()}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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

    # Copy audio to array (optional but good for archiving)
    # For now, just transcribe and save text
    
    print("Transcribing file...", end="\r")
    
    # Load audio using soundfile to get numpy array for consistent handling
    # or just use pywhispercpp's file handling
    # We want to use recorder's save_transcript logic
    
    try:
        import shutil
        filename = os.path.basename(file_path)
        
        # Determine save path using recorder logic
        if not recorder.base_path:
            recorder.base_path = recorder._find_storage_path()
            
        if recorder.base_path:
            save_dir = os.path.join(recorder.base_path, "Recordings")
            os.makedirs(save_dir, exist_ok=True)
            dest_path = os.path.join(save_dir, filename)
            
            if os.path.abspath(file_path) != os.path.abspath(dest_path):
                shutil.copy2(file_path, dest_path)
                print(f"Archived audio to: {filename}")
            
            # Convert to WAV if needed (for m4a, mp3, etc.)
            audio_path, needs_cleanup = convert_to_wav(file_path)
            
            try:
                import soundfile as sf
                import numpy as np
                
                data, samplerate = sf.read(audio_path)
                
                # Convert to mono if stereo
                if len(data.shape) > 1:
                    data = data.mean(axis=1)
                
                # Resample if not already 16kHz
                if samplerate != 16000:
                    import scipy.signal
                    num_samples = int(len(data) * 16000 / samplerate)
                    data = scipy.signal.resample(data, num_samples)
                    
                data = data.astype(np.float32)
                
                text = transcriber.transcribe(data)
            finally:
                # Clean up temp file if we created one
                if needs_cleanup and os.path.exists(audio_path):
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
    # Setup
    recorder = LiteRecorder()
    if "Volumes" not in str(recorder.base_path):
        print(f"📂 Storage: {recorder.base_path} (Local Mode)")
        print("   Note: Network drive not found, saving locally.")
        print("")
    else:
        print(f"📂 Storage: {recorder.base_path} (Network/Sync)")
        
    # Model path logic
    project_root = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(project_root, "models", "ggml-base.bin")
    
    # Check for smarter model
    smarter_model = os.path.join(project_root, "models", "ggml-small.en.bin")
    if os.path.exists(smarter_model):
        model_path = smarter_model
        print(f"✨ Using high-accuracy model: {os.path.basename(model_path)}")
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at: {model_path}")
        print("   Please run 'python download_models.py' first.")
        return

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

