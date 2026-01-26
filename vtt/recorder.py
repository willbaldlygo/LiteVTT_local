"""
Audio recording module for LiteScribe.
Handles recording, trimming, and saving to the dynamic array_main path.
"""

import os
import glob
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
from datetime import datetime

class LiteRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.channels = 1
        self._recording = False
        self._audio_buffer = []
        self._stream = None
        self.base_path = self._find_array_main()

    def _find_array_main(self):
        """Dynamically find the array_main mount point."""
        # Look for array_main* in /Volumes
        candidates = glob.glob("/Volumes/array_main*")
        
        for candidate in candidates:
            # Check for Lite_VTT folder
            vtt_path = os.path.join(candidate, "Lite_VTT")
            if os.path.isdir(vtt_path):
                return vtt_path
        
        # Fallback if not found (notify user later to check mount)
        return None

    def start(self):
        """Start recording."""
        # Ensure previous stream is closed
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"Warning: Failed to close previous stream: {e}")
            finally:
                self._stream = None

        self._audio_buffer = []
        self._recording = True
        
        def callback(indata, frames, time, status):
            if status:
                print(status)
            if self._recording:
                self._audio_buffer.append(indata.copy())
        
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback
            )
            self._stream.start()
        except Exception as e:
            print(f"Error starting recording stream: {e}")
            self._recording = False
            if self._stream:
                self._stream.close()
                self._stream = None
            raise e

    def stop(self):
        """Stop recording and return audio data."""
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
        
        if not self._audio_buffer:
            return None
            
        return np.concatenate(self._audio_buffer, axis=0)

    def save(self, audio_data, filename=None):
        """Save audio to the array_main/Lite_VTT/Lite_Scribe_Audio folder."""
        if self.base_path is None:
            # Re-check path in case it was mounted later
            self.base_path = self._find_array_main()
            
        if self.base_path is None:
            raise FileNotFoundError("Could not find 'Lite_VTT' folder in /Volumes/array_main*")

        save_dir = os.path.join(self.base_path, "Lite_Scribe_Audio")
        os.makedirs(save_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recording_{timestamp}.wav"
            
        full_path = os.path.join(save_dir, filename)
        sf.write(full_path, audio_data, self.sample_rate)
        return full_path, filename

    def save_transcript(self, text, audio_filename):
        """Save transcript to the array_main/Lite_VTT/Lite_Scribe_Transcripts folder."""
        if self.base_path is None:
            self.base_path = self._find_array_main()
            
        if self.base_path is None:
            raise FileNotFoundError("Could not find 'Lite_VTT' folder in /Volumes/array_main*")

        save_dir = os.path.join(self.base_path, "Lite_Scribe_Transcripts")
        os.makedirs(save_dir, exist_ok=True)
        
        # Replace extension with .txt
        base_name = os.path.splitext(audio_filename)[0]
        txt_filename = f"{base_name}.txt"
        
        full_path = os.path.join(save_dir, txt_filename)
        with open(full_path, "w") as f:
            f.write(text)
        return full_path

    def trim_silence(self, audio_data, threshold=0.01):
        """Basic silence trimming from start/end."""
        # TODO: Implement accurate VAD or energy-based trimming if needed
        # For now, simplistic amplitude check
        return audio_data  # Placeholder for V1, strictly requested features first
