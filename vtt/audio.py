"""Audio capture module for VTT Local.

Captures audio from the microphone and returns numpy arrays
suitable for Whisper transcription (16kHz mono float32).
"""

import numpy as np
import sounddevice as sd
from typing import Optional
import threading


class AudioRecorder:
    """Records audio from the default microphone."""

    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1  # Mono

    def __init__(self):
        self._recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def _audio_callback(self, indata: np.ndarray, frames: int,
                        time_info, status) -> None:
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"Audio status: {status}")
        if self._recording:
            with self._lock:
                self._audio_buffer.append(indata.copy())

    def start_recording(self) -> None:
        """Start capturing audio from the microphone."""
        # Ensure previous stream is closed
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"Warning: Failed to close previous stream: {e}")
            finally:
                self._stream = None

        with self._lock:
            self._audio_buffer = []

        try:
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype='float32',
                callback=self._audio_callback
            )
            self._recording = True
            self._stream.start()
        except Exception as e:
            print(f"Error starting recording stream: {e}")
            self._recording = False
            if self._stream:
                self._stream.close()
                self._stream = None
            raise e

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio as float32 at 16kHz."""
        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._audio_buffer:
                return np.array([], dtype=np.float32)

            # Concatenate all chunks and flatten to 1D
            audio = np.concatenate(self._audio_buffer, axis=0)
            audio = audio.flatten()
            self._audio_buffer = []

        return audio

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
