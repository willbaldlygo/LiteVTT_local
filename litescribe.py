#!/usr/bin/env python3
"""
LiteScribe - Recording & Transcription Tool
"""

import os
import sys
import time
from vtt.recorder import LiteRecorder
from vtt.transcriber import Transcriber

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
    file_path = input("> ").strip().replace("'", "").replace('"', "")
    
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
        # We need a dummy filename if we are not saving the audio itself
        # But wait, user wants "all audio files... stored in the array".
        # So we should copy the file to the array.
        
        import shutil
        filename = os.path.basename(file_path)
        
        # Determine save path using recorder logic
        if recorder.base_path is None:
            recorder.base_path = recorder._find_array_main()
            
        if recorder.base_path:
            save_dir = os.path.join(recorder.base_path, "Lite_Scribe_Audio")
            os.makedirs(save_dir, exist_ok=True)
            dest_path = os.path.join(save_dir, filename)
            
            if os.path.abspath(file_path) != os.path.abspath(dest_path):
                shutil.copy2(file_path, dest_path)
                print(f"Archived audio to: {filename}")
            
            # Now transcribe
            # To use existing transcriber class, we can load file or pass path
            # The current Transcriber class expects numpy array. 
            # Let's use internal pywhispercpp model directly or update Transcriber.
            # Easier to just use Transcriber.transcribe with numpy array loaded via soundfile
            
            import soundfile as sf
            import numpy as np
            import scipy.signal
            
            data, samplerate = sf.read(file_path)
            # Convert to mono/16k if needed
             # Convert to mono if stereo
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            if samplerate != 16000:
                num_samples = int(len(data) * 16000 / samplerate)
                data = scipy.signal.resample(data, num_samples)
                
            data = data.astype(np.float32)
            
            text = transcriber.transcribe(data)
            
            print("\n--- TRANSCRIPT ---")
            print(text)
            print("------------------")
            
            # Save Transcript
            txt_path = recorder.save_transcript(text, filename)
            print(f"Saved Transcript: {os.path.basename(txt_path)}")
            
        else:
            print("Error: Could not find array_main to save files.")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    # Setup
    recorder = LiteRecorder()
    if not recorder.base_path:
        print("⚠️  WARNING: Could not find 'Lite_VTT' folder in /Volumes/array_main*")
        print("   Recording/Transcription saving will likely fail.")
        print("   Please ensure the network drive is mounted.")
        print("")
    else:
        print(f"📂 Central Storage: {recorder.base_path}")
        
    model_path = os.path.join(os.path.dirname(__file__), "models", "ggml-base.bin")
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
