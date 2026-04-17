"""
Audio recording module for LiteScribe.
Handles recording and saving to configurable storage path.
"""

import os
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
from datetime import datetime

class LiteRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.channels = 1
        self._recording = False
        self._audio_buffer = []
        self._stream = None
        self.config = self._load_config()
        self.base_path = self._find_storage_path()

    def _load_config(self):
        """Load configuration from config.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        return {}

    def _find_storage_path(self):
        """Determine storage path: config override or default ~/Documents/LiteVTT/."""
        storage_cfg = self.config.get("storage", {})
        custom_path = storage_cfg.get("path", "").strip()

        if custom_path:
            base = os.path.expanduser(custom_path)
        else:
            base = os.path.expanduser("~/Documents/LiteVTT")

        try:
            os.makedirs(base, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create storage directory: {e}")

        return base

    def start(self):
        """Start recording."""
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
            print(f"Warning: Error starting recording stream: {e}")
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
            self._stream = None

        if not self._audio_buffer:
            return None

        return np.concatenate(self._audio_buffer, axis=0)

    def save(self, audio_data, filename=None):
        """Save audio to the storage folder."""
        if not self.base_path or not os.path.exists(self.base_path):
            self.base_path = self._find_storage_path()

        save_dir = os.path.join(self.base_path, "Recordings")
        os.makedirs(save_dir, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recording_{timestamp}.wav"

        full_path = os.path.join(save_dir, filename)
        sf.write(full_path, audio_data, self.sample_rate)
        return full_path, filename

    def save_transcript(self, text, audio_filename):
        """Save transcript to the storage folder."""
        if not self.base_path or not os.path.exists(self.base_path):
            self.base_path = self._find_storage_path()

        save_dir = os.path.join(self.base_path, "Transcripts")
        os.makedirs(save_dir, exist_ok=True)

        base_name = os.path.splitext(audio_filename)[0]
        txt_filename = f"{base_name}.txt"

        full_path = os.path.join(save_dir, txt_filename)
        with open(full_path, "w") as f:
            f.write(text)
        return full_path
